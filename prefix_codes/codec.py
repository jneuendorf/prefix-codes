from collections import Hashable
from typing import TypeVar, Generic

from prefix_codes.codes.base import Code
from prefix_codes.decoder import Decoder
from prefix_codes.encoder import Encoder

T = TypeVar('T', bound=Hashable)


class Codec(Generic[T]):
    code: Code[T]
    encoder: Encoder[T]
    decoder: Decoder[T]
    # codeword_table: dict[str, str]

    def __init__(self, code: Code[T]):
        self.code = code
        self.encoder = Encoder(code.get_table())
        self.decoder = Decoder(code)
        # self.codeword_table = codeword_table

    def encode(self, message: str) -> bytes:
        return self.encoder.encode(message)

    def decode(self, byte_stream: bytes, max_length: int = None) -> str:
        return ''.join(self.decoder.decode(byte_stream, max_length))

    @property
    def tree(self):
        return self.decoder.code.get_tree()
