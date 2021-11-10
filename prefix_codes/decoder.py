from collections import Hashable
from typing import TypeVar, Generic

from prefix_codes.binary_tree import BinaryTree
from prefix_codes.codes.base import Code
from prefix_codes.typedefs import BitGenerator
from prefix_codes.utils import read_bits

T = TypeVar('T', bound=Hashable)


class Decoder(Generic[T]):
    codeword_table: dict[str, str]
    code: Code[T]
    # tree: BinaryTree[T, Any]

    # def __init__(self, codeword_table: dict[str, str]):
    #     self.codeword_table = codeword_table
    #     self.tree = BinaryTree.from_codeword_table(codeword_table)
    def __init__(self, code: Code[T]):
        self.code = code
        # self.tree = code.get_tree()

    def decode(self, byte_stream: bytes, max_length: int = None) -> BitGenerator:
        node = self.code.get_tree()
        num_chars = 0
        for bit in read_bits(byte_stream):
            if max_length is not None and num_chars >= max_length:
                break

            char, node = node.consume_bit(bit)
            if char is not None:
                yield char
                num_chars += 1
