import sys
from argparse import ArgumentParser
from collections import OrderedDict
from pathlib import Path

from prefix_codes.codecs.base import BaseCodec
from prefix_codes.codecs.shannon_fano_elias import ShannonFanoEliasCodec
from prefix_codes.codecs.tree_based import TreeBasedCodec
from prefix_codes.codes.huffman import create_huffman_tree


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

        out_filename: Path = filename.with_suffix(f'{filename.suffix}.enc')
        assert not out_filename.exists(), f'{out_filename} already exists'

        with open(out_filename, 'wb') as outfile:
            outfile.write(codec.serialize(message))
    else:
        assert filename.suffix == '.enc', 'the encoded file extension must be ".enc"'
        out_filename: Path = (
            filename
            .with_suffix('')  # remove '.enc'
            .with_stem(f'{filename.with_suffix("").stem}_dec')  # add '_dec' to stem
        )
        assert not out_filename.exists(), f'{out_filename} already exists'

        with open(args.filename, 'rb') as file:
            byte_stream = file.read()

        codec: BaseCodec[int]  # bytes is an Iterable[int]
        match args.code:
            case 'huffman' | 'h':
                codec = TreeBasedCodec[int]
            case 'shannon-fano-elias' | 'sfe':
                codec = ShannonFanoEliasCodec[int]
            case _:
                raise ValueError('invalid code')

        decoded_message = bytes(codec.decode_byte_stream(byte_stream))
        with open(out_filename, 'wb') as outfile:
            outfile.write(decoded_message)
