import unittest

from prefix_codes.codec import Codec
from prefix_codes.codes.huffman import HuffmanCode
from prefix_codes.codes.manual import ManualCode


class TestStringMethods(unittest.TestCase):

    def setUp(self) -> None:
        self.manual_codec = Codec(ManualCode({
            'a': '00',
            'b': '01',
            'c': '100',
            'd': '101',
            'e': '110',
            'f': '111',
        }))

    def test_prefix_codes_codec(self):
        codec = self.manual_codec
        words = [
            'a',  # => 00 == 0
            'ab',  # => 10 00 == 8
            'ffa',  # => 00 111 111 == 63
            'deadbeef',  # => 111 110 110 01 101 00 110 101 = 111110 11001101 00110101 == 62 205 53
            'bad cafe bad face bed fed'.replace(' ', ''),
        ]

        for word in words:
            encoded = codec.encode(word)
            # print('word:', word)
            # print('encoded', ''.join(
            #     str(bit) for bit in reversed(list(read_bits(encoded)))
            # ))
            processed_word = codec.decode(encoded, max_length=len(word))
            assert processed_word == word, (
                f'incorrect decoding: expected {word} but got {processed_word}'
            )

    def test_prefix_codes_codec_with_invalid_chars(self):
        with self.assertRaises(AssertionError):
            self.manual_codec.encode('invalid characters!')

    def test_huffman_codec(self):
        """
        | a_k | p_k | codeword |
        |-----|-----|----------|
        | a   | .5  | 0        |
        | b   | .25 | 10       |
        | c   | .25 | 11       |
        l = 5/3 = 1,666
        """
        codec = Codec(HuffmanCode(b'aabc'))
        print('huffman tree', codec.tree)
        codeword_table = codec.code.get_table()
        print('huffman table', codeword_table)
        table: dict[str, str] = {
            chr(byte_value): codeword
            for byte_value, codeword in codeword_table.items()
        }
        self.assertEqual(len(table['a']), 1)
        self.assertEqual(len(table['b']), 2)
        self.assertEqual(len(table['c']), 2)
        # codec.encode()

