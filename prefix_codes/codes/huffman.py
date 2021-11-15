from prefix_codes.binary_tree import BinaryTree as Node
from prefix_codes.codes.base import Code
from prefix_codes.codes.base import T


class HuffmanCode(Code[T]):

    def get_tree(self) -> Node[T, float]:
        orphans: set[Node[T, float]] = {
            Node(terminal=symbol, meta=relative_freq)
            for symbol, relative_freq in self.get_relative_frequencies().items()
        }
        while len(orphans) >= 2:
            a, b = sorted(orphans, key=lambda item: item.meta)[:2]
            orphans -= {a, b}
            orphans |= {Node(children=[a, b], meta=a.meta + b.meta)}
        tree = orphans.pop()
        tree.set_root(tree)
        # print('huffman tree', tree)
        return tree


