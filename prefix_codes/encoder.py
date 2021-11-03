from prefix_codes.typedefs import BitStream
from prefix_codes.utils import write_bits, read_bits_from_string


class Encoder:
    codeword_table: dict[str, str]

    def __init__(self, codeword_table: dict[str, str]):
        self.codeword_table = codeword_table

    def encode(self, message: str) -> bytes:
        message_only_chars = set(message) - self.codeword_table.keys()
        assert not message_only_chars, f'message contains invalid characters: {message_only_chars}'
        bit_stream: BitStream = [
            bit
            for char in message
            for bit in read_bits_from_string(self.codeword_table[char])
        ]
        return write_bits(bit_stream)
