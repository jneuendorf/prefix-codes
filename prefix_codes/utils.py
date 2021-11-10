import itertools
from collections import Iterable
from typing import TypeVar

from prefix_codes.typedefs import BitStream, Bit

T = TypeVar('T')


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


def read_bits(message: bytes) -> BitStream:
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
