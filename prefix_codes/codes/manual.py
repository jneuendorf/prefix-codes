from typing import Any

from prefix_codes.binary_tree import BinaryTree
from prefix_codes.codes.base import Code


class ManualCode(Code[str]):

    # def __init__(self, codeword_table: dict[str, str]):
    #     super.__init__(codeword_table)

    def get_tree(self) -> BinaryTree[str, Any]:
        return BinaryTree.from_codeword_table(self.source)
