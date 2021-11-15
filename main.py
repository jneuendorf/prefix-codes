import pickle
from argparse import ArgumentParser
from math import ceil
from pathlib import Path
from typing import Any

from prefix_codes.binary_tree import BinaryTree
from prefix_codes.codec import Codec
from prefix_codes.codes.base import Code
from prefix_codes.codes.huffman import HuffmanCode
from prefix_codes.decoder import Decoder

NUM_BINARY_TREE_BYTES = 20
NUM_MESSAGE_BYTES = NUM_BINARY_TREE_BYTES * 2  # -> message_size <= tree_size**2

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

    filename: Path = args.filename

    if args.action == 'encode':
        with open(filename, 'rb') as file:
            message = file.read()

        code: Code[int]  # bytes is an Iterable[int]
        if args.code == 'huffman':
            code = HuffmanCode(message)
        else:
            raise ValueError('invalid code')

        codec = Codec(code)
        tree_bytes = pickle.dumps(codec.tree)
        tree_size = len(tree_bytes)
        assert ceil(tree_size.bit_length() / 8) <= NUM_BINARY_TREE_BYTES, (
            f'binary tree size is too large to be represented with {NUM_BINARY_TREE_BYTES} bytes'
        )
        tree_size_bytes = tree_size.to_bytes(length=NUM_BINARY_TREE_BYTES, byteorder='big')

        out_filename: Path = filename.with_suffix(f'{filename.suffix}.enc')
        assert not out_filename.exists(), f'{out_filename} already exists'

        encoded_message_bytes = codec.encode(message)
        message_size = sum(1 for _ in code.source)
        message_size_bytes = message_size.to_bytes(length=NUM_MESSAGE_BYTES, byteorder='big')
        assert ceil(message_size.bit_length() / 8) <= NUM_MESSAGE_BYTES, (
            f'message size is too large to be represented with {NUM_MESSAGE_BYTES} bytes'
        )
        print('binary tree size', tree_size)
        print('compression ratio',  message_size / len(encoded_message_bytes))
        with open(out_filename, 'wb') as outfile:
            outfile.write(
                tree_size_bytes + tree_bytes
                + message_size_bytes + encoded_message_bytes
            )
    else:
        assert filename.suffix == '.enc', 'the encoded file extension must be ".enc"'
        out_filename: Path = (
            filename
            .with_suffix('')  # remove '.enc'
            .with_stem(f'{filename.with_suffix("").stem}_dec')  # add '_dec' to stem
        )
        assert not out_filename.exists(), f'{out_filename} already exists'

        with open(args.filename, 'rb') as file:
            cursor = 0
            tree_size_bytes = file.read(NUM_BINARY_TREE_BYTES)
            tree_size = int.from_bytes(tree_size_bytes, byteorder='big')
            cursor += NUM_BINARY_TREE_BYTES

            file.seek(cursor)
            tree_bytes = file.read(tree_size)
            cursor += tree_size

            file.seek(cursor)
            message_size_bytes = file.read(NUM_MESSAGE_BYTES)
            message_size = int.from_bytes(message_size_bytes, byteorder='big')
            cursor += NUM_MESSAGE_BYTES

            file.seek(cursor)
            byte_stream = file.read()

        tree: BinaryTree[int, Any] = pickle.loads(tree_bytes)
        decoder: Decoder[int] = Decoder(tree)
        decoded_message = bytes(decoder.decode(byte_stream, max_length=message_size))

        with open(out_filename, 'wb') as outfile:
            outfile.write(decoded_message)
