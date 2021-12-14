from collections.abc import Iterator, Sequence
from typing import Iterable, Literal

from prefix_codes.codecs.base import BaseCodec
from prefix_codes.typedefs import Bit, BitStream
from prefix_codes.utils import write_bits, read_bits, H


class UnaryCodec(BaseCodec[H]):
    codeword_table: dict[H, BitStream]
    inverse_codeword_table: dict[tuple[Literal[0, 1], ...], H]

    def __init__(self, alphabet: Sequence[H]):
        self.codeword_table = {
            sample: [0]*n + [1]
            for n, sample in enumerate(alphabet)
        }
        self.inverse_codeword_table = {
            tuple(bit_stream): sample
            for sample, bit_stream in self.codeword_table.items()
        }

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
            bit_stream.extend(self.codeword_table[sample])
        return bit_stream

    def decode(self, byte_stream: bytes, *, max_length: int = None) -> Iterable[H]:
        bit_stream = read_bits(byte_stream)
        return (
            decoded
            for decoded, used in self.decode_bits(list(bit_stream), max_length=max_length)
        )

    def decode_bits(self, bit_stream: list[Bit], *, max_length: int = None) -> Iterator[tuple[H, int]]:
        yielded = 0
        while bit_stream:
            if max_length is not None and yielded >= max_length:
                break

            try:
                i = bit_stream.index(1) + 1
            except ValueError:
                # remaining bits of the bytes are all zeros
                break

            codeword = tuple(bit_stream[:i])
            bit_stream = bit_stream[i:]
            yield self.inverse_codeword_table[codeword], i
            yielded += 1

    def serialize_codec_data(self, message: Iterable[H]) -> bytes:
        raise NotImplementedError('UnaryCodec.serialize_codec_data')
