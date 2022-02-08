import itertools
import pickle
from collections import OrderedDict, Counter
from collections.abc import Iterable
from typing import cast

import numpy as np
import numpy.typing as npt
from scipy.fft import dct, idct

from prefix_codes.codecs.arithmetic import ArithmeticCodec
from prefix_codes.codecs.rice import RiceCodec
from prefix_codes.codecs.base import BaseCodec

IntArray = npt.NDArray[int]


# class TransformImageCodec(BaseCodec[IntArray]):
class TransformImageCodec(BaseCodec[int]):
    width: int
    height: int
    quantization_step_size: int
    block_size: int = 8
    lossless_codec = RiceCodec(
        R=3,
        # Yields 0, 1, -1, 2, -2, 3, -3, ...
        # This corresponds to the distribution of the quantization indexes.
        alphabet=[
            *itertools.chain.from_iterable(
                zip(
                    range(0, -129, -1),
                    range(1, 128))
            ),
            *[-127, -128]
        ],
    )

    # lossless_codec = ArithmeticCodec(
    #     U=6,
    #     V=8,
    #     probabilities=OrderedDict({
    #         val: 1 / 256
    #         for val in range(-128, 128)
    #     }),
    #     prefix_free=True,
    # )

    def __init__(self, width: int, height: int, quantization_step_size: int):
        super().__init__()
        self.width = width
        self.height = height
        self.quantization_step_size = quantization_step_size

    @classmethod
    def decode_byte_stream(cls, serialization: bytes) -> IntArray:
        width: int
        height: int
        quantization_step_size: int
        block_size: int

        codec_data, enc_message, message_length = cls.parse_byte_stream(serialization)
        width, height, quantization_step_size, block_size = pickle.loads(codec_data)
        # print('decoded meta data')
        # print(width, height, quantization_step_size, block_size)
        codec = cls(width, height, quantization_step_size)
        return codec.decode(enc_message, max_length=message_length)

    def encode(self, message: IntArray, *, max_length: int = None) -> bytes:
        # print('TransformImageCodec encode')
        # print(message)

        # u: IntArray = message - 128  # type: ignore
        # q: IntArray = np.around(u / self.quantization_step_size).astype(int).reshape(-1)  # type: ignore
        u = self.transform_enc(message)
        q: IntArray = (
            np.around(u / self.quantization_step_size)  # type: ignore
            .astype(int)
            .reshape(-1)
        )

        # clip quantization indexes to ensure they can be encoded using rice codes
        q = np.clip(q, -128, 127)

        # print('encode q', q.dtype)
        # print(q)
        # print(lossless_codec.R, len(bits), 'bytes')
        q_list = cast(list[int], q.tolist())
        # print(len(binary), 'bytes')
        print('encoded', q.size, 'elements')
        print('distinct count:', len(set(q_list)))
        # print(Counter(q_list))
        # print(np.min(q), np.max(q))
        # print(max(set(q_list) - {1985}))
        # print(q.tolist()[:50])
        return self.lossless_codec.encode(q_list, max_length=q.size)
        # binary = pickle.dumps(q_list)
        # return binary

    def transform_enc(self, message: IntArray) -> IntArray:
        assert message.ndim == 2, f'expected 2d input but got {message.ndim}'
        vertically_transformed = dct(message, axis=0, type=2)
        return dct(vertically_transformed, axis=1, type=2)

    def transform_dec(self, message: IntArray) -> IntArray:
        horizontally_transformed = idct(message, axis=1, type=2)
        return idct(horizontally_transformed, axis=0, type=2)

    def decode(self, byte_stream: bytes, *, max_length: int = None) -> IntArray:
        # q: IntArray = np.array(list(self.lossless_codec.decode(byte_stream, max_length=max_length)))
        # l: list[int] = pickle.loads(byte_stream)
        # print('ml', max_length)
        l: Iterable[int] = self.lossless_codec.decode(byte_stream, max_length=max_length)
        # print(list(l)[:50])
        # q: IntArray = np.array(l).reshape((self.height, self.width))
        q: IntArray = np.fromiter(l, dtype=int, count=self.height * self.width).reshape((self.height, self.width))
        # print('?????')
        # print(q, q.dtype)
        # print('decoded q', q.dtype)
        # print(q)
        # u: IntArray = q * self.quantization_step_size  # type: ignore
        # flat_message: IntArray = np.clip(u + 128, 0, 255)  # type: ignore
        # message: IntArray = flat_message.reshape((self.height, self.width))
        u: IntArray = q * self.quantization_step_size  # type: ignore
        # print(u, u.dtype)
        message = np.clip(self.transform_dec(u).astype(int), 0, 255)
        return message

    def serialize_codec_data(self, message: IntArray) -> bytes:
        return pickle.dumps(
            (self.width, self.height, self.quantization_step_size, self.block_size)
        )

    def get_message_length(self, message: IntArray) -> int:
        return message.size
