from decoder import Decoder
from encoder import Encoder


class Codec:
    encoder: Encoder
    decoder: Decoder
    codeword_table: dict[str, str]

    def __init__(self, codeword_table: dict[str, str]):
        self.encoder = Encoder(codeword_table)
        self.decoder = Decoder(codeword_table)
        self.codeword_table = codeword_table

    def encode(self, message: str) -> bytes:
        return self.encoder.encode(message)

    def decode(self, byte_stream: bytes, max_length: int = None) -> str:
        return ''.join(self.decoder.decode(byte_stream, max_length))

    @property
    def tree(self):
        return self.decoder.tree
