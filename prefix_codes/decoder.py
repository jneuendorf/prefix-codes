from collections import Hashable, Iterable
from typing import TypeVar, Generic, Any

from prefix_codes.binary_tree import BinaryTree
from prefix_codes.utils import read_bits

T = TypeVar('T', bound=Hashable)


class Decoder(Generic[T]):
    tree: BinaryTree[T, Any]

    def __init__(self, tree: BinaryTree):
        # self.code = code
        self.tree = tree

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
