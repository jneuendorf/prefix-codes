import pickle
from collections.abc import Iterable, Callable
from itertools import takewhile
from math import log2, ceil
from typing import Generic, OrderedDict, Literal

from prefix_codes.codecs.base import BaseCodec, T


class ShannonFanoEliasCodec(BaseCodec, Generic[T]):
    """See 05-SpecialVLCodes.pdf"""

    probabilities: OrderedDict[T, float]
    model: Literal['iid', 'markov', 'func']
    """Iterative refinement in practice, see slide 33"""
    is_prefix_free: bool

    def __init__(self, probabilities: OrderedDict[T, float], model: Literal['iid', 'markov', 'func'] = 'iid',
                 prefix_free: bool = False):
        self.probabilities = probabilities
        self.model = model
        self.is_prefix_free = prefix_free

    @classmethod
    def decode_byte_stream(cls, serialization: bytes) -> Iterable[T]:
        probabilities: OrderedDict[T, float]
        model: Literal['iid', 'markov', 'func']
        K: int

        codec_data, enc_message, message_length = cls.parse_byte_stream(serialization)
        probabilities, model, K = pickle.loads(codec_data)
        codec = cls(probabilities, model)
        return codec.decode(enc_message, num_bits=K, max_length=message_length)

    def serialize_codec_data(self, message: Iterable[T]) -> bytes:
        z, K = self.get_z_and_K(message)
        return pickle.dumps([self.probabilities, self.model, K])

    def get_z_and_K(self, message: Iterable[T]) -> tuple[int, int]:
        W = 1
        L = 0
        for i, symbol in enumerate(message):
            prev_symbols = message[:i]
            p = self.p(symbol, prev_symbols)
            L += W * self.c(symbol, prev_symbols)
            W *= p

        K = ceil(-log2(W))
        if self.is_prefix_free:
            K += 1
        z = ceil(L * 2 ** K)

        return z, K

    def encode(self, message: Iterable[T]) -> bytes:
        """See slide 34.
        W: interval width W_i, the current value in W_0, ..., W_N
        L: lower interval bound L_i, the current value in L_0, ..., L_N
        z: integer value of the codeword
        K: number of bits in codeword
        """

        assert all(symbol in self.probabilities for symbol in message), 'message contains invalid symbols'

        z, K = self.get_z_and_K(message)
        return z.to_bytes(ceil(K / 8), byteorder='big')

    def decode(self, byte_stream: bytes, *, max_length: int = None, num_bits: int = None) -> Iterable[T]:
        """See slide 36."""
        if num_bits is None:
            M = len(byte_stream) * 8
        else:
            M = num_bits

        z = int.from_bytes(byte_stream, byteorder='big')
        v = z * (2 ** (-M))
        W = 1
        L = 0

        symbols = list(self.probabilities)
        for i in range(max_length):
            k = 0
            # TODO: what to pass as condition?
            U = L + W * self.p(symbols[k], [])
            while v >= U:
                k += 1
                U = U + W * self.p(symbols[k], [])
            W = W * self.p(symbols[k], [])
            L = U - W
            yield symbols[k]

    @property
    def p(self) -> Callable[[T, Iterable[T]], float]:
        match self.model:
            case 'iid':
                return self.p_iid
            case _:
                raise NotImplementedError('todo')

    def p_iid(self, symbol: T, prev_symbols: Iterable[T]):
        return self.probabilities[symbol]

    @property
    def c(self) -> Callable[[T, Iterable[T]], float]:
        match self.model:
            case 'iid':
                return self.c_iid
            case _:
                raise NotImplementedError('todo')

    def c_iid(self, symbol: T, prev_symbols: Iterable[T]):
        return sum(
            p for _, p in takewhile(
                lambda item: item[0] != symbol,
                self.probabilities.items(),
            )
        )
