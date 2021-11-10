from collections import Hashable, Iterable
from typing import TypeVar, Generic

from prefix_codes.typedefs import BitStream
from prefix_codes.utils import write_bits, read_bits_from_string

T = TypeVar('T', bound=Hashable)


class Encoder(Generic[T]):
    codeword_table: dict[T, str]

    def __init__(self, codeword_table: dict[T, str]):
        self.codeword_table = codeword_table

    def encode(self, message: Iterable[T]) -> bytes:
        message_only_chars = set(message) - self.codeword_table.keys()
        assert not message_only_chars, f'message contains invalid characters: {message_only_chars}'
        bit_stream: BitStream = [
            bit
            for char in message
            for bit in read_bits_from_string(self.codeword_table[char])
        ]
        return write_bits(bit_stream)
