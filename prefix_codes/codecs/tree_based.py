import pickle
from collections.abc import Iterable
from typing import Generic, Any

from prefix_codes.binary_tree import BinaryTree
from prefix_codes.codecs.base import T, BaseCodec
from prefix_codes.typedefs import BitStream
from prefix_codes.utils import write_bits, read_bits_from_string, read_bits, get_relative_frequencies


class TreeBasedCodec(BaseCodec, Generic[T]):
    """Uses a codeword instance that uses a tree in order
    to represent a codeword table.
    """

    tree: BinaryTree[T, Any]
    table: dict[T, str]

    def __init__(self, tree: BinaryTree[T, Any], table: dict[T, str]):
        self.tree = tree
        self.table = table

    @classmethod
    def from_tree(cls, tree: BinaryTree[T, Any]):
        return cls(tree, tree.get_table())

    @classmethod
    def from_table(cls, table: dict[T, str]):
        return cls(BinaryTree.from_table(table), table)

    @classmethod
    def decode_byte_stream(cls, serialization: bytes) -> Iterable[T]:
        codec_data, enc_message, message_length = cls.parse_byte_stream(serialization)
        codec = cls.from_tree(pickle.loads(codec_data))
        return codec.decode(enc_message, max_length=message_length)

    def serialize_codec_data(self, message: Iterable[T]) -> bytes:
        return pickle.dumps(self.tree)

    def encode(self, message: Iterable[T]) -> bytes:
        message_only_chars = set(message) - self.table.keys()
        assert not message_only_chars, f'message contains invalid characters: {message_only_chars}'
        bit_stream: BitStream = [
            bit
            for char in message
            for bit in read_bits_from_string(self.table[char])
        ]
        return write_bits(bit_stream)

    def decode(self, byte_stream: bytes, max_length: int = None) -> Iterable[T]:
        node = self.tree
        num_chars = 0
        for bit in read_bits(byte_stream):
            if max_length is not None and num_chars >= max_length:
                break

            terminal, node = node.consume_bit(bit)
            if terminal is not None:
                yield terminal
                num_chars += 1

    def get_average_codeword_length(self, message: Iterable[T]) -> float:
        table = self.table
        relative_frequencies = get_relative_frequencies(message)
        return sum(
            relative_frequencies[symbol] * len(codeword)
            for symbol, codeword in table.items()
        )
