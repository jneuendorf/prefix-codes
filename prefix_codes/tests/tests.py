import unittest
from collections import OrderedDict
from unittest import skip

import numpy as np

from prefix_codes.codecs.arithmetic import ArithmeticCodec
from prefix_codes.codecs.predictive import optimal_affine_predictor, optimal_affine_predictor_statistics
from prefix_codes.codecs.shannon_fano_elias import ShannonFanoEliasCodec
from prefix_codes.codecs.tree_based import TreeBasedCodec
from prefix_codes.codes.huffman import create_huffman_tree
from prefix_codes.utils import read_bits, get_relative_frequencies


class TestCodecs(unittest.TestCase):

    @skip('')
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

    @skip('')
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

    @skip('')
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

    @skip('')
    def test_huffmann_codec_average_codeword_length(self):
        message = b'aabc'
        codec = TreeBasedCodec.from_tree(create_huffman_tree(message))
        self.assertEqual(codec.get_average_codeword_length(message), 1.5)

    @skip('')
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

    @skip('')
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

    @skip('')
    def test_huffman_encode_decode_file(self):
        max_length = 2 ** 10
        with open('prefix_codes/tests/englishText.txt', 'rb') as file:
            message = file.read(max_length)
        codec = TreeBasedCodec.from_tree(create_huffman_tree(message))
        self.assertEqual(
            bytes(codec.decode(codec.encode(message), max_length=max_length)),
            message
        )

    @skip('')
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

    @skip('')
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

    @skip('')
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

    @skip('')
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

    @skip('')
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
        print(
            '[arithmetic] binary representation of encode("BANANA") =',
            bin(int.from_bytes(encoded, byteorder='big')),
            f'({K} bits)',
        )
        self.assertEqual(
            ''.join([str(bit) for bit in read_bits(encoded)][:K]),
            '110100000',
        )

    @skip('')
    def test_arithmetic_encode_decode(self):
        A = ord('A')
        N = ord('N')
        B = ord('B')
        codec: ArithmeticCodec[int] = ArithmeticCodec(
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
        encoded = codec.encode(message, max_length=len(message))
        # K = codec.get_num_codeword_bits(message)
        K = 9
        self.assertEqual(
            bytes(codec.decode(encoded, num_bits=K, max_length=len(message))),
            message
        )

    @skip('')
    def test_arithmetic_with_audio_file(self):
        with open('prefix_codes/tests/Queen_sint8.raw', 'rb') as file:
            message = file.read()

        num_samples = len(message)
        relative_frequencies: dict[int, float] = get_relative_frequencies(message)
        codec: ArithmeticCodec[int] = ArithmeticCodec(
            U=24,
            V=24,
            probabilities=OrderedDict(relative_frequencies),
        )
        # pprint(relative_frequencies)
        compression_ratio = num_samples / len(codec.encode(message, max_length=num_samples))
        self.assertGreater(compression_ratio, 1)

    def test_predictive_codec_predictor_nirvana(self):
        """07-PredictiveCoding.pdf, slide 24"""

        with open('prefix_codes/tests/Nirvana_sint16.raw', 'rb') as file:
            message = file.read()

        data = np.array([
            # (unsigned - 256 if unsigned > 127 else unsigned)
            # for unsigned in message
            int.from_bytes(message[i:i+2], byteorder='little', signed=True)
            for i in range(0, len(message), 2)
        ])
        # print(data)

        stats = optimal_affine_predictor_statistics(
            data,
            correlations=[
                (-1,),
                (-2,),
                (-3,),
            ],
        )
        print(stats)

    @skip('')
    def test_predictive_codec_predictor_lena(self):
        """07-PredictiveCoding.pdf, slide 28"""

        with open('prefix_codes/tests/lena512.pgm', 'rb') as file:
            lines: list[bytes] = file.readlines()

        assert len(lines) == 4, 'invalid format'
        img_type = lines[0].strip(b'\n').decode('ascii')
        assert img_type == 'P5', f'expected image type "P5" but got "{img_type}"'

        size = lines[1].strip(b'\n').decode('ascii').split()
        width = int(size[0])
        height = int(size[1])
        max_sample_value = int(lines[2].strip(b'\n').decode('ascii'))
        assert max_sample_value == 255, (
            f'expected 8-bit samples but got max sample value {max_sample_value}'
        )
        data: list[int] = list(lines[3])
        img = np.array(data).reshape((height, width))
        print(img)

        stats = optimal_affine_predictor_statistics(
            np.array(img),
            correlations=[
                # (y, x)
                (0, -1),  # hor
                (-1, 0),  # ver
                (-1, -1),  # al
                (-1, 1),  # ar
            ],
        )
        print(stats)

        # pred = optimal_affine_predictor(
        #     np.array(list(message)),
        #     observations=[
        #         lambda index: (index[0] - 1,),
        #         lambda index: (index[0] - 2,),
        #     ],
        # )

    @skip('')
    def test_predictive_codec_predictor(self):
        pred = optimal_affine_predictor(
            np.array([0, 1, 2, 3, 0, 4, 1, 5, 6, 7, 8, 9]),
            observations=[
                lambda index: (index[0] - 1,),
                lambda index: (index[0] - 2,),
            ],
        )
        print('prediction for i=0', pred((5,)))
