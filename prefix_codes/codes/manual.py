from typing import Any

from prefix_codes.binary_tree import BinaryTree
from prefix_codes.codes.base import Code


class ManualCode(Code[str]):
    """Codeword table is given as source."""

    def get_tree(self) -> BinaryTree[str, Any]:
        return BinaryTree.from_codeword_table(self.source)
