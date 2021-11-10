import unittest
from pprint import pprint

from prefix_codes.codec import Codec
from prefix_codes.codes.huffman import HuffmanCode
from prefix_codes.codes.manual import ManualCode
from prefix_codes.utils import read_bits


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
        self.words = [
            'a',  # => 00 == 0
            'ab',  # => 10 00 == 8
            'ffa',  # => 00 111 111 == 63
            'deadbeef',  # => 111 110 110 01 101 00 110 101 = 111110 11001101 00110101 == 62 205 53
            'bad cafe bad face bed fed'.replace(' ', ''),
        ]

    def test_manual_codec_correctness(self):
        """
        words = [
            'a',  # => 00 == 0
            'ab',  # => 10 00 == 8
            'ffa',  # => 00 111 111 == 63
            'deadbeef',  # => 111 110 110 01 101 00 110 101 = 111110 11001101 00110101 == 62 205 53
            'bad cafe bad face bed fed'.replace(' ', ''),
        ]
        """
        codec = self.manual_codec

        for word in self.words:
            encoded = codec.encode(word)
            # print('word:', word)
            # print('encoded', ''.join(
            #     str(bit) for bit in reversed(list(read_bits(encoded)))
            # ))
            processed_word = ''.join(codec.decode(encoded, max_length=len(word)))
            self.assertEqual(processed_word, word)

    def test_prefix_codes_codec_with_invalid_chars(self):
        with self.assertRaises(AssertionError):
            self.manual_codec.encode('invalid characters!')

    def test_huffman_codec_correctness(self):
        """
        | a_k | p_k | codeword |
        |-----|-----|----------|
        | a   | .5  | 0        |
        | b   | .25 | 10       |
        | c   | .25 | 11       |
        l = 5/3 = 1,666
        """
        message = b'aabc'
        codec = Codec(HuffmanCode(message))
        # print('huffman tree', codec.tree)
        encoded = codec.encode(message)
        # print(encoded)
        # print('encoded', ''.join(
        #     str(bit) for bit in reversed(list(read_bits(encoded)))
        # ))
        decoded = codec.decode(encoded, max_length=len(message))
        self.assertEqual(bytes(decoded), message)

    def test_huffmann_codec_average_codeword_length(self):
        message = b'aabc'
        codec = Codec(HuffmanCode(message))
        self.assertEqual(codec.average_codeword_length, 1.5)

    def test_huffmann_codec_table(self):
        message = b'aabc'
        codec = Codec(HuffmanCode(message))
        table: dict[str, str] = {
            chr(byte_value): codeword
            for byte_value, codeword in codec.table.items()
        }
        self.assertEqual(table.keys(), {'a', 'b', 'c'})
        self.assertEqual(len(table['a']), 1)
        self.assertEqual(len(table['b']), 2)
        self.assertEqual(len(table['c']), 2)

    def test_huffman_with_file_english_text(self):
        with open('prefix_codes/tests/englishText.txt', 'rb') as file:
            message = file.read()
        codec = Codec(HuffmanCode(message))
        print('------------------------------------------------------')
        print('Codeword table for prefix_codes/tests/englishText.txt:')
        pprint(codec.table)
        print('-------------------------')
        print('Average code word length:')
        print(codec.average_codeword_length)
        self.assertAlmostEqual(codec.average_codeword_length, 4.596, places=3)

    def test_huffman_with_file_image_data(self):
        with open('prefix_codes/tests/imageData.raw', 'rb') as file:
            message = file.read()
        codec = Codec(HuffmanCode(message))
        print('------------------------------------------------------')
        print('Codeword table for prefix_codes/tests/englishText.txt:')
        pprint(codec.table)
        print('-------------------------')
        print('Average code word length:')
        print(codec.average_codeword_length)
        self.assertAlmostEqual(codec.average_codeword_length, 7.634, places=3)
