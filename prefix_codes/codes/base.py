import itertools
from abc import ABC, abstractmethod
from collections import Iterable, Hashable, Counter
from typing import TypeVar, Generic, Any

from prefix_codes.binary_tree import BinaryTree

T = TypeVar('T', bound=Hashable)


class Code(ABC, Generic[T]):

    def __init__(self, source: Iterable[T]):
        self.source = self.read_source(source)

    @staticmethod
    def read_source(source: Iterable[T], max_length: int = None) -> Iterable[T]:
        if max_length is None:
            return source
        else:
            assert max_length >= 0, '"max_length" must be positive'
            return itertools.islice(source, max_length)

    # @property
    # def symbol_set(self) -> set[T]:
    #     return set(self.source)

    @abstractmethod
    def get_tree(self) -> BinaryTree[T, Any]:
        ...

    def get_table(self) -> dict[T, str]:
        def traverse(node, path: str):
            if node.terminal is not None:
                table[node.terminal] = path
            else:
                if node[0]:
                    traverse(node[0], f'{path}0')
                if node[1]:
                    traverse(node[1], f'{path}1')

        table: dict[T, str] = {}
        traverse(self.get_tree(), '')
        return table

    def get_relative_frequencies(self) -> dict[T, int]:
        counter = Counter(self.source)
        n = sum(counter.values())
        return {
            symbol: count / n
            for symbol, count in counter.items()
        }

    @property
    def average_codeword_length(self) -> float:
        table = self.get_table()
        relative_frequencies = self.get_relative_frequencies()
        return sum(
            relative_frequencies[symbol] * len(codeword)
            for symbol, codeword in table.items()
        )
