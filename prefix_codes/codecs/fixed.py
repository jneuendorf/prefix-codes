from typing import Iterable, Sequence

from prefix_codes.codecs.base import BaseCodec
from prefix_codes.typedefs import Bit, BitStream
from prefix_codes.utils import write_bits, read_bits, H, chunk


class FixedCodec(BaseCodec):
    num_bits: int
    alphabet: Sequence[H]

    def __init__(self, alphabet: Sequence[H]):
        self.alphabet = alphabet
        self.num_bits = (len(alphabet) - 1).bit_length()

    @classmethod
    def decode_byte_stream(cls, serialization: bytes) -> Iterable[H]:
        raise NotImplementedError('FixedCodec.decode_byte_stream')

    def encode(self, message: Iterable[H], *, max_length: int = None) -> bytes:
        return write_bits(self.encode_to_bits(message, max_length=max_length))

    def encode_to_bits(self, message: Iterable[H], *, max_length: int = None) -> BitStream:
        bit_stream: list[Bit] = []
        for i, sample in enumerate(message):
            if max_length is not None and i >= max_length:
                break
            bit_stream.extend(self.get_codeword(sample))
        return bit_stream

    def get_codeword(self, sample: H) -> list[Bit]:
        n = self.alphabet.index(sample)
        num = self.num_bits
        bit_stream: list[Bit] = []
        while num:
            num -= 1
            bit = (n >> num) & 1
            bit_stream.append(bit)
        return bit_stream

    def decode(self, byte_stream: bytes, *, max_length: int = None) -> Iterable[H]:
        if self.num_bits == 0:
            return []

        bit_stream = read_bits(byte_stream)
        yield from self.decode_bits(bit_stream, max_length=max_length)

    def decode_bits(self, bit_stream: BitStream, *, max_length: int = None) -> list[H]:
        if self.num_bits == 0:
            return []

        decoded_samples: list[H] = []
        for codeword in chunk(bit_stream, self.num_bits):
            if max_length is not None and len(decoded_samples) >= max_length:
                break

            codeword = list(codeword)
            n = 0
            num = self.num_bits
            while num:
                num -= 1
                n <<= 1
                n += codeword.pop(0)
            decoded_samples.append(self.alphabet[n])

        return decoded_samples

    def serialize_codec_data(self, message: Iterable[H]) -> bytes:
        raise NotImplementedError('FixedCodec.serialize_codec_data')
