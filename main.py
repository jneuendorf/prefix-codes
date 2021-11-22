import sys
from argparse import ArgumentParser
from collections import OrderedDict
from math import ceil
from pathlib import Path

from prefix_codes.codecs.base import BaseCodec
from prefix_codes.codecs.shannon_fano_elias import ShannonFanoEliasCodec
from prefix_codes.codecs.tree_based import TreeBasedCodec
from prefix_codes.codes.huffman import create_huffman_tree

NUM_BINARY_TREE_BYTES = 20
NUM_MESSAGE_BYTES = NUM_BINARY_TREE_BYTES * 2  # -> message_size <= tree_size**2

if __name__ == '__main__':
    parser = ArgumentParser(description='Decode or encode files')
    parser.add_argument(
        'code',
        choices=[
            'huffman', 'h',
            'shannon-fano-elias', 'sfe',
        ],
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

    filename: Path = args.filename

    if args.action == 'encode':
        with open(filename, 'rb') as file:
            message = file.read()

        codec: BaseCodec[int]  # bytes is an Iterable[int]
        match args.code:
            case 'huffman' | 'h':
                # codec = Codec(HuffmanCode(message))
                # codec = TreeBasedCodec.from_code(HuffmanCode(message))
                codec = TreeBasedCodec.from_tree(create_huffman_tree(message))
            case 'shannon-fano-elias' | 'sfe':
                codec = ShannonFanoEliasCodec(OrderedDict([
                    (ord('a'), 1 / 2),
                    (ord('n'), 1 / 3),
                    (ord('b'), 1 / 6),
                ]))
                print(codec.encode(b'banana'))
                sys.exit(0)
            case _:
                raise ValueError('invalid code')

        codec_bytes = codec.serialize()
        num_codec_bytes = len(codec_bytes)
        assert ceil(num_codec_bytes.bit_length() / 8) <= NUM_BINARY_TREE_BYTES, (
            f'binary tree size is too large to be represented with {NUM_BINARY_TREE_BYTES} bytes'
        )
        codec_bytes_size = num_codec_bytes.to_bytes(length=NUM_BINARY_TREE_BYTES, byteorder='big')

        out_filename: Path = filename.with_suffix(f'{filename.suffix}.enc')
        assert not out_filename.exists(), f'{out_filename} already exists'

        encoded_message_bytes = codec.encode(message)
        message_size = sum(1 for _ in message)
        message_size_bytes = message_size.to_bytes(length=NUM_MESSAGE_BYTES, byteorder='big')
        assert ceil(message_size.bit_length() / 8) <= NUM_MESSAGE_BYTES, (
            f'message size is too large to be represented with {NUM_MESSAGE_BYTES} bytes'
        )
        print('binary tree size', num_codec_bytes)
        print('compression ratio',  message_size / len(encoded_message_bytes))
        with open(out_filename, 'wb') as outfile:
            outfile.write(
                codec_bytes_size + codec_bytes
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
            codec_bytes_size = file.read(NUM_BINARY_TREE_BYTES)
            num_codec_bytes = int.from_bytes(codec_bytes_size, byteorder='big')
            cursor += NUM_BINARY_TREE_BYTES

            file.seek(cursor)
            codec_bytes = file.read(num_codec_bytes)
            cursor += num_codec_bytes

            file.seek(cursor)
            message_size_bytes = file.read(NUM_MESSAGE_BYTES)
            message_size = int.from_bytes(message_size_bytes, byteorder='big')
            cursor += NUM_MESSAGE_BYTES

            file.seek(cursor)
            byte_stream = file.read()

        # tree: BinaryTree[int, Any] = pickle.loads(codec_bytes)
        codec: BaseCodec[int]  # bytes is an Iterable[int]
        match args.code:
            case 'huffman' | 'h':
                codec = TreeBasedCodec.deserialize(codec_bytes)
            case 'shannon-fano-elias' | 'sfe':
                codec = ShannonFanoEliasCodec(OrderedDict([
                    (ord('a'), 1 / 2),
                    (ord('n'), 1 / 3),
                    (ord('b'), 1 / 6),
                ]))
                print(codec.encode(b'banana'))
                sys.exit(0)
            case _:
                raise ValueError('invalid code')

        decoded_message = bytes(codec.decode(byte_stream, max_length=message_size))
        with open(out_filename, 'wb') as outfile:
            outfile.write(decoded_message)
