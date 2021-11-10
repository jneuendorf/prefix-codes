from collections import Hashable, Iterable
from typing import TypeVar, Generic

from prefix_codes.codes.base import Code
from prefix_codes.decoder import Decoder
from prefix_codes.encoder import Encoder

T = TypeVar('T', bound=Hashable)


class Codec(Generic[T]):
    code: Code[T]
    encoder: Encoder[T]
    decoder: Decoder[T]

    def __init__(self, code: Code[T]):
        self.code = code
        self.encoder = Encoder(code.get_table())
        self.decoder = Decoder(code)

    def encode(self, message: Iterable[T]) -> bytes:
        return self.encoder.encode(message)

    def decode(self, byte_stream: bytes, max_length: int = None) -> Iterable[T]:
        return self.decoder.decode(byte_stream, max_length)

    @property
    def table(self):
        return self.code.get_table()

    @property
    def tree(self):
        return self.code.get_tree()

    @property
    def average_codeword_length(self) -> float:
        return self.code.average_codeword_length
