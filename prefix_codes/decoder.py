from collections import Generator
from typing import Literal

from binary_tree import BinaryTree

Bit = Literal[0, 1]


class Decoder:
    codeword_table: dict[str, str]
    tree: BinaryTree

    def __init__(self, codeword_table: dict[str, str]):
        self.codeword_table = codeword_table
        self.tree = BinaryTree.from_codeword_table(codeword_table)

    def decode(self, message: bytes) -> Generator[str, None, None]:
        # assert not set(message) - self.codeword_table.keys(), (
        #     f'message contains characters {set(message) - self.codeword_table.keys()} '
        #     'which not defined in the codeword table'
        # )
        node = self.tree
        for bit in self.read_bits(message):
            char, node = node.consume_bit(bit)
            yield char

    def read_bits(self, message: bytes) -> Generator[Bit, None, None]:
        """Read the bits from a file, low bits first.
        See https://stackoverflow.com/a/2577487/6928824
        """

        for byte in message:
            for i in range(8):
                yield (byte >> i) & 1
