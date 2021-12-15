from collections.abc import Iterator
from typing import Iterable, Sequence

from prefix_codes.codecs.arithmetic import bit_string
from prefix_codes.codecs.base import BaseCodec
from prefix_codes.typedefs import Bit, BitStream
from prefix_codes.utils import write_bits, read_bits, H, read_bits_from_string, chunk


class FixedCodec(BaseCodec):
    num_bits: int
    alphabet: Sequence[H]
    codeword_table: dict[H, BitStream]

    def __init__(self, alphabet: Sequence[H]):
        self.num_bits = (len(alphabet) - 1).bit_length()
        self.codeword_table = {
            sample: list(read_bits_from_string(
                bit_string(n, self.num_bits)
            ))
            for n, sample in enumerate(alphabet)
        }
        self.inverse_codeword_table = {
            tuple(bit_stream): sample
            for sample, bit_stream in self.codeword_table.items()
        }

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
            bit_stream.extend(self.codeword_table[sample])
        return bit_stream

    def decode(self, byte_stream: bytes, *, max_length: int = None) -> Iterable[H]:
        bit_stream = read_bits(byte_stream)
        yield from self.decode_bits(bit_stream, max_length=max_length)

    def decode_bits(self, bit_stream: BitStream, *, max_length: int = None) -> Iterator[H]:
        yielded = 0
        for codeword in chunk(bit_stream, self.num_bits):
            if max_length is not None and yielded >= max_length:
                break

            yield self.inverse_codeword_table[codeword]
            yielded += 1

    def serialize_codec_data(self, message: Iterable[H]) -> bytes:
        raise NotImplementedError('FixedCodec.serialize_codec_data')
