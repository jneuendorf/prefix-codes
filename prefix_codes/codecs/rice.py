from collections.abc import Collection, Iterable, Sequence

from prefix_codes.codecs.arithmetic import bit_string
from prefix_codes.codecs.fixed import FixedCodec
from prefix_codes.codecs.unary import UnaryCodec
from prefix_codes.codecs.base import BaseCodec
from prefix_codes.utils import H, write_bits, read_bits
from prefix_codes.typedefs import Bit, BitStream


class RiceCodec(BaseCodec[H]):
    R: int
    alphabet: Sequence[H]

    def __init__(self, R: int, alphabet: Sequence[H]):
        assert R >= 0, 'Rice parameter must be greater or equal to zero'
        self.R = R
        self.alphabet = alphabet
        # print('Rice -> R =', R)
        # print(list(range(2 ** R)))

        self.unary_codec: UnaryCodec[int] = UnaryCodec(list(range(len(alphabet))))
        self.fixed_codec: FixedCodec[int] = FixedCodec(list(range(2 ** R)))

    @classmethod
    def auto_encode(cls, message: Iterable[H], alphabet: Sequence[H], R_max: int = 5) -> tuple['RiceCodec', bytes]:
        best_codec: RiceCodec | None = None
        shortest_bit_stream: BitStream | None = None
        l = float('inf')

        for R in range(R_max):
            codec = cls(R, alphabet)
            bit_stream = codec.encode_to_bits(message)
            current_l = len(list(bit_stream))
            if current_l < l:
                best_codec = codec
                shortest_bit_stream = bit_stream
                l = current_l
        return best_codec, write_bits(shortest_bit_stream)

    @classmethod
    def decode_byte_stream(cls, serialization: bytes) -> Iterable[H]:
        raise NotImplementedError('RiceCodec.decode_byte_stream')

    def encode(self, message: Iterable[H], *, max_length: int = None) -> bytes:
        return write_bits(self.encode_to_bits(message, max_length=max_length))

    def encode_to_bits(self, message: Iterable[H], *, max_length: int = None) -> list[Bit]:
        bit_stream: list[Bit] = []
        for i, sample in enumerate(message):
            if max_length is not None and i >= max_length:
                break
            bit_stream.extend(self.get_codeword(sample))
        return bit_stream

    def get_codeword(self, sample: H) -> BitStream:
        n = self.alphabet.index(sample)
        prefix = n >> self.R
        suffix = n - (prefix << self.R)
        bit_stream: list[Bit] = []
        bit_stream.extend(self.unary_codec.encode_to_bits([prefix]))
        bit_stream.extend(self.fixed_codec.encode_to_bits([suffix]))
        return bit_stream

    def decode(self, byte_stream: bytes, *, max_length: int = None) -> Iterable[H]:
        bit_stream = read_bits(byte_stream)
        yielded = 0
        while True:
            if max_length is not None and yielded >= max_length:
                break

            # decode next unary-encoded piece
            try:
                prefix = next(self.unary_codec.decode_bits(bit_stream, max_length=1))
            except StopIteration:
                break

            # unary_used_bits = prefix + 1

            fixed_used_bits = self.fixed_codec.num_bits
            if fixed_used_bits:
                suffix = next(self.fixed_codec.decode_bits(bit_stream, max_length=1))
            else:  # R = 0 => no fixed-length code. Thus, no used bits and suffix = 0 because it doesn't change n
                suffix = 0

            n = (prefix << self.R) + suffix
            yield self.alphabet[n]
            yielded += 1

    def serialize_codec_data(self, message: Iterable[H]) -> bytes:
        raise NotImplementedError('RiceCodec.serialize_codec_data')
