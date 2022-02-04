import pickle
from collections import OrderedDict

import numpy as np
import numpy.typing as npt

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
    # lossless_codec = RiceCodec(R=3, alphabet=list(range(-128, 128)))
    lossless_codec = ArithmeticCodec(
        U=6,
        V=8,
        probabilities=OrderedDict({
            val: 1 / 256
            for val in range(-128, 128)
        }),
        prefix_free=True,
    )

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
        u: IntArray = message - 128  # type: ignore
        q: IntArray = np.around(u / self.quantization_step_size).astype(int).reshape(-1)  # type: ignore
        # print('encode q', q.dtype)
        # print(q)
        # print(lossless_codec.R, len(bits), 'bytes')
        # return self.lossless_codec.encode(q, max_length=q.size)
        binary = pickle.dumps(q)
        # print(len(binary), 'bytes')
        print('encoded', q.size, 'elements')
        print('distinct count:', len(set(q.tolist())))
        return binary

    def decode(self, byte_stream: bytes, *, max_length: int = None) -> IntArray:
        # q: IntArray = np.array(list(self.lossless_codec.decode(byte_stream, max_length=max_length)))
        q: IntArray = pickle.loads(byte_stream)
        # print('decoded q', q.dtype)
        # print(q)
        u: IntArray = q * self.quantization_step_size  # type: ignore
        flat_message: IntArray = u + 128  # type: ignore
        flat_message = np.clip(flat_message, 0, 255)
        message: IntArray = flat_message.reshape((self.height, self.width))
        return message

    def serialize_codec_data(self, message: IntArray) -> bytes:
        return pickle.dumps(
            (self.width, self.height, self.quantization_step_size, self.block_size)
        )

    def get_message_length(self, message: IntArray) -> int:
        return message.size
