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

        # python3.9 main.py huffman encode prefix_codes/tests/englishText.txt
        # Namespace(code='huffman', action='encode', filename=PosixPath('prefix_codes/tests/englishText.txt'))
        # size of tree: 6143
        # b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x17\xff'
        # ROOT[ROOT[ROOT[101, ROOT[ROOT[ROOT[ROOT[ROOT[84, ROOT[ROOT[68, 63], ROOT[79, 113]]], ROOT[45, 73]], ROOT[ROOT[ROOT[83, ROOT[33, ROOT[53, ROOT[ROOT[93, 42], ROOT[88, ROOT[ROOT[ROOT[ROOT[ROOT[ROOT[ROOT[126, 60], ROOT[62, 94]], 37], ROOT[9, ROOT[38, 64]]], 43], 90], ROOT[81, ROOT[36, 47]]]]]]]], ROOT[120, 80]], ROOT[ROOT[ROOT[70, ROOT[89, 52]], ROOT[106, ROOT[51, 56]]], ROOT[39, ROOT[95, 49]]]]], ROOT[44, 121]], 115]], ROOT[ROOT[105, 110], ROOT[ROOT[ROOT[112, 103], ROOT[119, ROOT[ROOT[ROOT[ROOT[82, 69], ROOT[ROOT[76, ROOT[74, ROOT[35, ROOT[124, 91]]]], 66]], ROOT[65, ROOT[ROOT[50, 48], 67]]], 118]]], 111]]], ROOT[ROOT[ROOT[97, ROOT[108, 100]], ROOT[116, ROOT[ROOT[ROOT[ROOT[ROOT[ROOT[77, 87], ROOT[ROOT[71, ROOT[85, 75]], 78]], 34], 46], 102], ROOT[109, 10]]]], ROOT[32, ROOT[ROOT[ROOT[13, ROOT[ROOT[ROOT[ROOT[ROOT[ROOT[40, 41], 59], ROOT[122, ROOT[61, 58]]], ROOT[72, ROOT[ROOT[86, 55], ROOT[54, 57]]]], 107], 98]], ROOT[117, 99]], ROOT[104, 114]]]]]

        sys.stdout.buffer.write(
            tree_size_bytes
            + tree_bytes
            + codec.encode(message)
        )
    else:
        ...


