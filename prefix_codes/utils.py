import itertools
from collections import Counter
from collections.abc import Hashable, Iterable, Iterator
from os import PathLike
from typing import TypeVar

import numpy as np
import numpy.typing as npt

from prefix_codes.typedefs import BitStream, Bit

T = TypeVar('T')
H = TypeVar('H', bound=Hashable)


def get_bit(byte: int, i: int) -> Bit:
    return (byte >> i) & 1


def set_bit(byte: int, i: int, bit: Bit) -> int:
    """See https://stackoverflow.com/a/12174051/6928824"""
    mask = (1 << i)
    return (byte & ~mask) | (bit << i)


def get_byte(bit_stream: BitStream) -> int:
    byte = 0
    for i, bit in enumerate(bit_stream):
        assert 0 <= i < 8, 'bit stream is too long'
        byte = set_bit(byte, i, bit)
    return byte


def read_bits(message: Iterable[int]) -> Iterator[Bit]:
    # return ((byte >> i) & 1 for byte in message for i in range(8))
    return (get_bit(byte, i) for byte in message for i in range(8))


def read_bits_from_string(s: str) -> BitStream:
    assert all(char in ('0', '1') for char in set(s)), f'Expected bit string but got "{s}"'
    return (int(char) for char in s)


def chunk(collection: Iterable[T], n: int) -> Iterable[Iterable[T]]:
    return itertools.zip_longest(*[iter(collection)]*n, fillvalue=0)


def write_bits(bit_stream: BitStream) -> bytes:
    """Inverse of `read_bits`."""
    return bytes(
        get_byte(bits) for bits in chunk(bit_stream, n=8)
    )


def get_relative_frequencies(message: Iterable[H]) -> dict[H, float]:
    counter = Counter(message)
    n = sum(counter.values())
    return {
        symbol: count / n
        for symbol, count in counter.items()
    }


def parse_binary_pgm(filename: PathLike | str) -> tuple[npt.NDArray[int], int, int]:
    with open(filename, 'rb') as file:
        lines: list[bytes] = file.readlines()

    assert len(lines) == 4, 'invalid format'
    img_type = lines[0].strip(b'\n').decode('ascii')
    assert img_type == 'P5', f'expected image type "P5" but got "{img_type}"'

    size = lines[1].strip(b'\n').decode('ascii').split()
    width = int(size[0])
    height = int(size[1])
    max_sample_value = int(lines[2].strip(b'\n').decode('ascii'))
    assert max_sample_value == 255, f'expected 8-bit samples but got max sample value {max_sample_value}'
    data: list[int] = list(lines[3])
    img = np.array(data).reshape(height, width)

    return img, width, height


def img_to_binary_pgm(img: npt.NDArray[int], width: int, height: int) -> bytes:
    max_value = np.max(img)
    assert max_value <= 255, f'expected 8-bit samples but got max sample value {max_value}'
    return b'\n'.join([
        'P5'.encode('ascii'),
        f'{width} {height}'.encode('ascii'),
        '255'.encode('ascii'),
        bytes(img.reshape(-1).tolist()),
    ])
