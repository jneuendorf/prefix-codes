import pickle
import sys
from argparse import ArgumentParser
from pathlib import Path

from prefix_codes.codes.huffman import HuffmanCode
from prefix_codes.codes.base import Code
from prefix_codes.codec import Codec
from prefix_codes.utils import read_bits


NUM_BINARY_TREE_BYTES = 20


if __name__ == '__main__':
    parser = ArgumentParser(description='Decode or encode files')
    parser.add_argument(
        'code',
        choices=['huffman'],
        type=str,
        help='code to use',
    )
    parser.add_argument(
        'action',
        choices=['encode', 'decode'],
        type=str,
        help='encode or decode',
    )
    parser.add_argument(
        'filename',
        type=Path,
        help='path to the file to be processed',
    )

    args = parser.parse_args()
    print(args)

    with open(args.filename, 'rb') as file:
        message = file.read()

    if args.action == 'encode':
        code: Code
        if args.code == 'huffman':
            code = HuffmanCode(message)
        else:
            raise ValueError('invalid code')

        codec = Codec(code)
        tree_bytes = pickle.dumps(codec.tree)
        n = len(tree_bytes)
        tree_size_bytes = n.to_bytes(length=NUM_BINARY_TREE_BYTES, byteorder='big')
        print('size of tree:', n)
        print(tree_size_bytes)

        sys.stdout.buffer.write(
            tree_size_bytes
            + tree_bytes
            + codec.encode(message)
        )
    else:
        ...


