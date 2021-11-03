from collections import Counter, Iterable, Generator
from math import ceil, log2
from typing import Literal, Sequence, Optional

Bit = Literal[0, 1]
CodewordLenghts = dict[str, int]
# Code = Literal['shannon']


def str2bits(s: str) -> Sequence[Bit]:
    assert all(char in ('0', '1') for char in set(s)), f'Expected bit string but got "{s}"'
    return [int(char) for char in s]  # noqa


# def shannon_code(codeword_table: dict[str, str], message: str) -> CodewordLenghts:
#     n = len(message)
#     counter = Counter(message)
#     relative_frequencies = {
#         terminal: count / n
#         for terminal, count in counter.items()
#     }
#     return {
#         terminal: ceil(-log2(relative_frequencies[terminal]))
#         for terminal in counter
#     }


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
        # message: str = '',
        # code: Code = 'shannon',
    ) -> 'BinaryTree':
        # assert not (
        #         set(message) - codeword_table.keys()), 'message contains characters not defined in the codeword table'
        # if code == 'shannon':
        #     codeword_lengths = shannon_code(codeword_table, message)
        # else:
        #     raise NotImplementedError(f'Code {code} not implemented')
        root = cls(root=None)
        for terminal, codeword in codeword_table.items():
            root.add_terminal(str2bits(codeword), terminal)
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

    def add_terminal(self, bit_sequence: Iterable[Bit], terminal: str, replace=False) -> None:
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

    # def parse(self, bits: Iterable[Bit]) -> Generator[str]:
    #     node = self.root
    def consume_bit(self, bit: Bit) -> tuple[str, 'BinaryTree']:
        if self.terminal:
            return self.terminal, self.root
        else:
            assert self[bit] is not None, f'could not consume bit {bit}'
            return '', self[bit]
