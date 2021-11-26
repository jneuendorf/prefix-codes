import itertools
from collections import OrderedDict
from collections.abc import Iterable
from typing import Generic

from prefix_codes.codecs.base import T
from prefix_codes.codecs.shannon_fano_elias import ShannonFanoEliasCodec, ModelType
from prefix_codes.typedefs import BitStream, Bit
from prefix_codes.utils import set_bit, write_bits, read_bits_from_string, read_bits


def bit_string(n: int, bits: int = 0) -> str:
    # NOTE: Default means as many bits as necessary (because specifying less than necessary is impossible)
    return format(n, f'0{bits}b')


def leading_zeros(n: int, bits: int) -> int:
    try:
        return bit_string(n, bits).index('1')
    except ValueError:
        return bits


def trailing_ones(n: int, bits: int) -> int:
    try:
        return bit_string(n, bits).rindex('0')
    except ValueError:
        return bits


def handle_carry(n: int, bits: int, c: int) -> tuple[int, int, BitStream]:
    bit_stream: list[Bit] = []
    carry = int(bit_string(n, bits)[0])
    if carry == 1:
        n = set_bit(n, bits, 0)
        bit_stream.append(1)
        c -= 1
        if c > 1:
            bit_stream.extend([0] * (c - 1))
    return n, c, bit_stream


class ArithmeticCodec(ShannonFanoEliasCodec, Generic[T]):
    """See 06-ArithmeticCoding.pdf"""

    V: int
    """Bits to use for representing probability masses"""
    U: int
    """Bits to use for representing interval widths"""
    p_V: dict[T, float]
    """Quantized probability masses with V bits"""
    c_V: dict[T, float]
    """Quantized cumulative probabilities (cmf/cdf) with V bits"""

    def __init__(self, probabilities: OrderedDict[T, float], model: ModelType = 'iid',
                 prefix_free: bool = False, V: int = 4, U: int = 4):
        super().__init__(probabilities, model, prefix_free)
        self.V = V
        self.U = U
        self.quantize_probabilities()

    def quantize_probabilities(self):
        self.p_V = {
            symbol: round(prob * (2 ** self.V))
            for symbol, prob in self.probabilities.items()
        }
        accumulated_ps = list(itertools.accumulate(self.p_V.values(), initial=0))
        self.c_V = {
            symbol: accumulated_ps[i]
            for i, symbol in enumerate(self.probabilities)
        }
        assert sum(self.p_V.values()) <= 2 ** self.V, 'invalid quantization'

    def get_num_codeword_bits(self, message: Iterable[T]) -> int:
        a = 1 if self.is_prefix_free else 0
        return a + z_n - self.U + 1

    def encode(self, message: Iterable[T]) -> bytes:
        V = self.V
        U = self.U

        # INIT
        A = 2 ** U - 1
        B = 0
        c = 0
        mask = (1 << (U + V)) - 1

        bit_stream: list[Bit] = []

        # ITERATIVE ENCODING
        for symbol in message:
            # CALCULATE
            A_ast = A * self.p_V[symbol]
            B_ast = B + A * self.c_V[symbol]

            # DETERMINE NUMBER OF LEADING ZERO BITS
            delta_z = leading_zeros(A_ast, U + V)

            # CHECK FOR CARRY BIT
            B_ast, c, new_bits = handle_carry(B_ast, U + V + 1, c)
            bit_stream.extend(new_bits)

            # INVESTIGATE delta_z LEADING ZERO BITS
            if delta_z > 0:
                B_ast_z_leading_bits = bit_string(B_ast, U + V)[:delta_z]
                n_1 = trailing_ones(int(B_ast_z_leading_bits, 2), delta_z)
                if n_1 < delta_z:
                    bit_stream.extend(read_bits_from_string(bit_string(c)))
                    bit_stream.extend(
                        read_bits_from_string(B_ast_z_leading_bits[:-n_1 - 1])
                    )
                    c = n_1 + 1
                elif n_1 == delta_z and c > 0:
                    c += n_1
                elif n_1 == delta_z and c == 0:
                    bit_stream.extend(read_bits_from_string(B_ast_z_leading_bits))
                    c = 0

            # UPDATE PARAMETERS
            A = A_ast >> (V - delta_z)
            B = (B_ast << delta_z) & mask

        # CODEWORD TERMINATION
        a = 1 if self.is_prefix_free else 0
        X = U + V - a - 1
        if '1' in bit_string(B, U + V)[-X:]:
            B += (1 << X)
            B, c, new_bits = handle_carry(B, U + V, c)
            bit_stream.extend(new_bits)
        bit_stream.append(0)
        bit_stream.extend([1] * (c - 1))
        B_most_significant_bits = bit_string(B, U + V)[:a]
        bit_stream.extend(read_bits_from_string(B_most_significant_bits))

        return write_bits(bit_stream)

    def decode(self, byte_stream: bytes, *, max_length: int = None, num_bits: int = None) -> Iterable[T]:
        V = self.V
        U = self.U

        # INIT
        A = 2 ** U - 1
        u = int(
            ''.join(
                str(bit) for bit in itertools.islice(read_bits(byte_stream), U + V)
            ),
            base=2,
        )

        # ITERATIVE DECODING
        for symbol in self.probabilities:
            # IDENTIFY NEXT SYMBOL
            U = A * (self.c_V[symbol] + self.p_V[symbol])
            if u < U:
                yield symbol
                break

            # UPDATE PARAMETERS
            A_ast = A * self.p_V[symbol]
            delta_z = leading_zeros(A_ast, U + V)
            u = (u - A * self.c_V[symbol]) << delta_z
            A = A_ast >> (V - delta_z)
