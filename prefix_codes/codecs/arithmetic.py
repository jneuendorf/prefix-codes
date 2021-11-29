import itertools
from collections import OrderedDict
from collections.abc import Iterable
from typing import Generic

from tqdm import tqdm

from prefix_codes.codecs.base import T
from prefix_codes.codecs.shannon_fano_elias import ShannonFanoEliasCodec, ModelType
from prefix_codes.typedefs import BitStream, Bit
from prefix_codes.utils import set_bit, write_bits, read_bits_from_string, read_bits


def bit_string(n: int, bits: int = 0) -> str:
    # NOTE: Default means as many bits as necessary
    # (because specifying less than necessary is impossible)
    return format(n, f'0{bits}b')


def leading_zeros(n: int, bits: int) -> int:
    try:
        return bit_string(n, bits).index('1')
    except ValueError:
        return bits


def trailing_ones(n: int, bits: int) -> int:
    try:
        return bits - bit_string(n, bits).rindex('0') - 1
    except ValueError:
        return bits


def handle_carry(n: int, bits: int, c: int) -> tuple[int, int, BitStream]:
    bit_stream: list[Bit] = []
    carry = int(bit_string(n, bits)[0])
    if carry == 1:
        n -= (1 << (bits - 1))

        bit_stream.append(1)
        c -= 1
        if c > 1:
            bit_stream.extend([0] * (c - 1))
            c = 1
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

    def encode(self, message: Iterable[T], *, max_length: int = None) -> bytes:
        V = self.V
        U = self.U

        # INIT
        A = 2 ** U - 1
        B = 0
        c = 0
        mask = (1 << (U + V)) - 1
        # print('init')
        # print('A', A)
        # print('c', c)
        # print('B', B)

        bit_stream: list[Bit] = []

        # ITERATIVE ENCODING
        for symbol in tqdm(message, total=max_length):
            # print('loop')
            # CALCULATE
            A_ast = A * self.p_V[symbol]
            B_ast = B + A * self.c_V[symbol]
            # print('A*', A_ast)
            # print('B*', B_ast)

            # DETERMINE NUMBER OF LEADING ZERO BITS
            delta_z = leading_zeros(A_ast, U + V)
            # print('∆z', delta_z)

            # CHECK FOR CARRY BIT
            B_ast, c, new_bits = handle_carry(B_ast, U + V + 1, c)
            # print('carry?', B_ast, new_bits)
            bit_stream.extend(new_bits)
            # print('update bitstream', bit_stream)

            # INVESTIGATE delta_z LEADING ZERO BITS
            if delta_z > 0:
                # print('B* binary', bit_string(B_ast, U + V))
                B_ast_z_leading_bits = bit_string(B_ast, U + V)[:delta_z]
                # print('∆z leading B*', B_ast_z_leading_bits)
                n_1 = trailing_ones(int(B_ast_z_leading_bits, base=2), delta_z)
                # print('n_1', n_1)
                if n_1 < delta_z:
                    # print('case 1')
                    # output c outstanding bits
                    if c > 0:
                        bit_stream.append(0)
                        c -= 1
                    while c > 0:
                        bit_stream.append(1)
                        c -= 1
                    # bit_stream.extend(read_bits_from_string(bit_string(c)))
                    # print('update bitstream', bit_stream)
                    # output first ∆z - n_1 - 1 bits of B*
                    bit_stream.extend(
                        read_bits_from_string(B_ast_z_leading_bits[:-n_1 - 1])
                    )
                    # print('update bitstream', bit_stream)
                    c = n_1 + 1
                elif n_1 == delta_z and c > 0:
                    # print('case 2')
                    c += n_1
                elif n_1 == delta_z and c == 0:
                    # print('case 3')
                    bit_stream.extend(read_bits_from_string(B_ast_z_leading_bits))
                    # print('update bitstream', bit_stream)
                    c = 0
                # print('update bitstream', bit_stream)
                # print('updated c', c)

            # UPDATE PARAMETERS
            A = A_ast >> (V - delta_z)
            B = (B_ast << delta_z) & mask
            # print('A', A)
            # print('B', B)
            # print('--------------------\n')

        # CODEWORD TERMINATION
        # print('terminate')
        a = 1 if self.is_prefix_free else 0
        X = U + V - a - 1
        if '1' in bit_string(B, U + V)[-X:]:
            B += (1 << X)  # round up lower interval boundary
            # print('B', bin(B))
        B, c, new_bits = handle_carry(B, U + V + 1, c)
        # print('B', bin(B))
        # B_ast = B + (1 << X)
        # B_ast, c, new_bits = handle_carry(B_ast, U + V + 1, c)
        # print('updated c', c)
        bit_stream.extend(new_bits)

        # print('update bitstream', bit_stream)
        # output all outstanding bits
        bit_stream.append(0)
        bit_stream.extend([1] * (c - 1))
        # print('update bitstream', bit_stream)
        B_most_significant_bits = bit_string(B, U + V)[:a + 1]
        bit_stream.extend(read_bits_from_string(B_most_significant_bits))
        # print('final bitstream', bit_stream)

        return write_bits(bit_stream)

    def decode(self, byte_stream: bytes, *, max_length: int = None, num_bits: int = None) -> Iterable[T]:
        V = self.V
        UV = self.U + self.V

        # INIT
        A = 2 ** self.U - 1
        u = int(
            ''.join(
                str(bit) for bit in itertools.islice(read_bits(byte_stream), UV)
            ),
            base=2,
        )
        # print('init')
        # print(A, u)

        # ITERATIVE DECODING
        for n in range(max_length):
            # IDENTIFY NEXT SYMBOL
            for symbol in self.probabilities:
                U = A * (self.c_V[symbol] + self.p_V[symbol])
                # print(f'U({symbol})', U)
                if u < U:
                    # print('output', symbol)
                    yield symbol

                    # UPDATE PARAMETERS
                    A_ast = A * self.p_V[symbol]
                    # print('A*', A_ast)
                    u_ast = u - A * self.c_V[symbol]
                    # print('u*', u_ast)
                    delta_z = leading_zeros(A_ast, UV)
                    # print('∆z', delta_z)
                    u = (u - A * self.c_V[symbol]) << delta_z
                    A = A_ast >> (V - delta_z)

                    break
