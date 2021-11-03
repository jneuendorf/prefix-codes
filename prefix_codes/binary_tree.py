from typing import Optional

from prefix_codes.typedefs import Bit, BitStream
from utils import read_bits_from_string


class BinaryTree(list[Optional['BinaryTree']]):
    terminal: str = None
    root: 'BinaryTree' = None

    def __init__(self, root: Optional['BinaryTree']):
        super().__init__([None, None])
        self.root = root if root is not None else self

    @classmethod
    def from_codeword_table(
        cls,
        codeword_table: dict[str, str],
    ) -> 'BinaryTree':
        root = cls(root=None)
        for terminal, codeword in codeword_table.items():
            root.add_terminal(read_bits_from_string(codeword), terminal)
        return root

    def __delitem__(self, key: Bit):
        assert key in (0, 1), f'Invalid index {key}'
        self[key] = None  # noqa

    def __setitem__(self, key: Bit, value: 'BinaryTree'):
        assert key in (0, 1), f'Invalid index {key}'
        assert isinstance(value, BinaryTree), f'Invalid value {value}'
        super().__setitem__(key, value)

    def __repr__(self):
        if self.terminal is not None:
            return self.terminal
        return f'{"ROOT" if self.is_root else ""}{super().__repr__()}'

    @property
    def is_root(self):
        return self.root is self

    def add_terminal(self, bit_sequence: BitStream, terminal: str, replace=False) -> None:
        if not bit_sequence:
            if self.terminal is not None and not replace:
                raise ValueError(f'Cannot set terminal {terminal} because ode already has terminal {self.terminal}')
            else:
                self.terminal = terminal
            return

        bit, *bits = bit_sequence
        if not self[bit]:
            self[bit] = type(self)(root=self.root)
        self[bit].add_terminal(bits, terminal, replace=replace)

    def consume_bit(self, bit: Bit) -> tuple[Optional[str], 'BinaryTree']:
        """Goes to the next node according to `bit` and returns it and the according character."""
        assert self[bit] is not None, f'could not consume bit {bit}'
        next_node = self[bit]
        if next_node.terminal:
            return next_node.terminal, self.root
        else:
            return None, next_node
