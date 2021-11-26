import unittest
from collections import OrderedDict

from prefix_codes.codecs.arithmetic import ArithmeticCodec
from prefix_codes.codecs.shannon_fano_elias import ShannonFanoEliasCodec
from prefix_codes.codecs.tree_based import TreeBasedCodec
from prefix_codes.codes.huffman import create_huffman_tree


class TestCodecs(unittest.TestCase):

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
        codec = TreeBasedCodec.from_table({
            'a': '00',
            'b': '01',
            'c': '100',
            'd': '101',
            'e': '110',
            'f': '111',
        })
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
            processed_word = ''.join(codec.decode(encoded, max_length=len(word)))
            self.assertEqual(processed_word, word)

    def test_prefix_codes_codec_with_invalid_chars(self):
        with self.assertRaises(AssertionError):
            codec = TreeBasedCodec.from_table({
                'a': '00',
                'b': '01',
                'c': '100',
                'd': '101',
                'e': '110',
                'f': '111',
            })
            codec.encode('invalid characters!')

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
        codec = TreeBasedCodec.from_tree(create_huffman_tree(message))
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
        codec = TreeBasedCodec.from_tree(create_huffman_tree(message))
        self.assertEqual(codec.get_average_codeword_length(message), 1.5)

    def test_huffmann_codec_table(self):
        message = b'aabc'
        codec = TreeBasedCodec.from_tree(create_huffman_tree(message))
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
        codec = TreeBasedCodec.from_tree(create_huffman_tree(message))
        # print('------------------------------------------------------')
        # print('Codeword table for prefix_codes/tests/englishText.txt:')
        # pprint(codec.table)
        # print('-------------------------')
        # print('Average code word length:')
        # print(codec.average_codeword_length)
        self.assertAlmostEqual(codec.get_average_codeword_length(message), 4.596, places=3)

    def test_huffman_encode_decode_file(self):
        max_length = 2 ** 10
        with open('prefix_codes/tests/englishText.txt', 'rb') as file:
            message = file.read(max_length)
        codec = TreeBasedCodec.from_tree(create_huffman_tree(message))
        self.assertEqual(
            bytes(codec.decode(codec.encode(message), max_length=max_length)),
            message
        )

    def test_huffman_with_file_image_data(self):
        with open('prefix_codes/tests/imageData.raw', 'rb') as file:
            message = file.read()
        codec = TreeBasedCodec.from_tree(create_huffman_tree(message))
        # print('------------------------------------------------------')
        # print('Codeword table for prefix_codes/tests/englishText.txt:')
        # pprint(codec.table)
        # print('-------------------------')
        # print('Average code word length:')
        # print(codec.average_codeword_length)
        self.assertAlmostEqual(codec.get_average_codeword_length(message), 7.634, places=3)

    def test_shannon_fano_elias_encode_decode(self):
        message = b'banana'
        probabilities = OrderedDict([
            (ord('a'), 1 / 2),
            (ord('n'), 1 / 3),
            (ord('b'), 1 / 6),
        ])
        codec = ShannonFanoEliasCodec(probabilities, model='iid')
        encoded = codec.encode(message)
        K = codec.get_num_codeword_bits(message)
        self.assertEqual(
            encoded,
            int('111000100', 2).to_bytes(len(encoded), byteorder='big'),
        )
        self.assertEqual(
            bytes(codec.decode(encoded, num_bits=K, max_length=len(message))),
            message
        )

    def test_shannon_fano_elias_exercise(self):
        message = b'REFEREE'
        probabilities = OrderedDict([
            (ord('E'), 5 / 8),
            (ord('R'), 2 / 8),
            (ord('F'), 1 / 8),
        ])
        codec = ShannonFanoEliasCodec(probabilities, model='iid', prefix_free=True)
        encoded = codec.encode(message)
        K = codec.get_num_codeword_bits(message)
        print(
            '[shannon_fano_elias] binary representation of encode("REFEREE") =',
            bin(int.from_bytes(encoded, byteorder='big')),
            f'({K} bits)',
        )

        self.assertEqual(
            bytes(codec.decode(encoded, num_bits=K, max_length=len(message))),
            message
        )

    def test_arithmetic_quantization(self):
        A = ord('A')
        N = ord('N')
        B = ord('B')
        codec = ArithmeticCodec(
            V=4,
            U=4,
            probabilities=OrderedDict([
                (A, 1 / 2),
                (N, 1 / 3),
                (B, 1 / 6),
            ]),
        )
        self.assertEqual(codec.p_V, {A: 8, N: 5, B: 3})
        self.assertEqual(codec.c_V, {A: 0, N: 8, B: 13})

    def test_arithmetic_encode(self):
        A = ord('A')
        N = ord('N')
        B = ord('B')
        codec = ArithmeticCodec(
            V=4,
            U=4,
            probabilities=OrderedDict([
                (A, 1 / 2),
                (N, 1 / 3),
                (B, 1 / 6),
            ]),
            prefix_free=False,
        )
        message = b'BANANA'
        encoded = codec.encode(message)
        # K = codec.get_num_codeword_bits(message)
        K = 9
        print(bin(encoded[0]))
        print(bin(encoded[1]))
        print(
            '[arithmetic] binary representation of encode("BANANA") =',
            bin(int.from_bytes(encoded, byteorder='big')),
            f'({K} bits)',
        )
        # self.assertEqual(
        #     encoded,
        #     int('110100000', 2).to_bytes(len(encoded), byteorder='big'),
        # )
        # self.assertEqual(encoded, b'')

    def test_arithmetic_encode_decode(self):
        A = ord('A')
        N = ord('N')
        B = ord('B')
        codec = ArithmeticCodec(
            V=4,
            U=4,
            probabilities=OrderedDict([
                (A, 1 / 2),
                (N, 1 / 3),
                (B, 1 / 6),
            ]),
            prefix_free=False,
        )
        message = b'BANANA'
        encoded = codec.encode(message)
        # K = codec.get_num_codeword_bits(message)
        K = 9
        self.assertEqual(
            bytes(codec.decode(encoded, num_bits=K, max_length=len(message))),
            message
        )
