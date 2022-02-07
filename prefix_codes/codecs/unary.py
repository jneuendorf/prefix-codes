from collections.abc import Sequence
from typing import Iterable

from prefix_codes.codecs.base import BaseCodec
from prefix_codes.typedefs import Bit, BitStream
from prefix_codes.utils import write_bits, read_bits, H


class UnaryCodec(BaseCodec[H]):
    alphabet: Sequence[H]

    def __init__(self, alphabet: Sequence[H]):
        self.alphabet = alphabet

    @classmethod
    def decode_byte_stream(cls, serialization: bytes) -> Iterable[H]:
        raise NotImplementedError('UnaryCodec.decode_byte_stream')

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
        bit_stream: list[Bit] = []
        while n:
            n -= 1
            bit_stream.append(0)
        return bit_stream + [1]

    def decode(self, byte_stream: bytes, *, max_length: int = None) -> Iterable[H]:
        bit_stream = read_bits(byte_stream)
        return (
            decoded
            for decoded, used in self.decode_bits(list(bit_stream), max_length=max_length)
        )

    def decode_bits(self, bit_stream: list[Bit], *, max_length: int = None) -> list[H]:
        decoded_samples: list[H] = []
        while bit_stream:
            if max_length is not None and len(decoded_samples) >= max_length:
                break

            if 1 in bit_stream:
                n = bit_stream.index(1)
            # remaining bits of the bytes are all zeros
            else:
                break

            decoded_samples.append(self.alphabet[n])

        return decoded_samples

    def serialize_codec_data(self, message: Iterable[H]) -> bytes:
        raise NotImplementedError('UnaryCodec.serialize_codec_data')
