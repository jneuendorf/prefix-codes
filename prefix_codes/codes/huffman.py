from collections.abc import Iterable

from prefix_codes.binary_tree import BinaryTree as Node, BinaryTree
from prefix_codes.codecs.base import T
from prefix_codes.utils import get_relative_frequencies


def create_huffman_tree(message: Iterable[T]) -> BinaryTree[T, float]:
    orphans: set[Node[T, float]] = {
        Node(terminal=symbol, meta=relative_freq)
        for symbol, relative_freq in get_relative_frequencies(message).items()
    }
    while len(orphans) >= 2:
        a, b = sorted(orphans, key=lambda item: item.meta)[:2]
        orphans -= {a, b}
        orphans |= {Node(children=[a, b], meta=a.meta + b.meta)}
    tree = orphans.pop()
    tree.set_root(tree)
    # print('huffman tree', tree)
    return tree
