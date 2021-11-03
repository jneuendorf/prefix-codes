from prefix_codes.binary_tree import BinaryTree
from prefix_codes.typedefs import BitGenerator
from prefix_codes.utils import read_bits


class Decoder:
    codeword_table: dict[str, str]
    tree: BinaryTree

    def __init__(self, codeword_table: dict[str, str]):
        self.codeword_table = codeword_table
        self.tree = BinaryTree.from_codeword_table(codeword_table)

    def decode(self, byte_stream: bytes) -> BitGenerator:
        node = self.tree
        for bit in read_bits(byte_stream):
            char, node = node.consume_bit(bit)
            yield char
