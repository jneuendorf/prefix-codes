from prefix_codes.binary_tree import BinaryTree
from prefix_codes.typedefs import BitGenerator
from prefix_codes.utils import read_bits


class Decoder:
    codeword_table: dict[str, str]
    tree: BinaryTree

    def __init__(self, codeword_table: dict[str, str]):
        self.codeword_table = codeword_table
        self.tree = BinaryTree.from_codeword_table(codeword_table)

    def decode(self, byte_stream: bytes, max_length: int = None) -> BitGenerator:
        node = self.tree
        num_chars = 0
        for bit in read_bits(byte_stream):
            if max_length is not None and num_chars >= max_length:
                break

            char, node = node.consume_bit(bit)
            if char is not None:
                yield char
                num_chars += 1
