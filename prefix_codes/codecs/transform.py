from typing import Iterable

import numpy.typing as npt

from prefix_codes.codecs.base import BaseCodec, T


class TransformImageCodec(BaseCodec[npt.NDArray[int]]):
    block_size: int = 8
    quantization_step_size: float
    width: int
    height: int

    def __init__(self, quantization_step_size: float):
        self.quantization_step_size = quantization_step_size

    @classmethod
    def decode_byte_stream(cls, serialization: bytes) -> Iterable[T]:
        pass

    def encode(self, message: Iterable[T], *, max_length: int = None) -> bytes:
        pass

    def decode(self, byte_stream: bytes, *, max_length: int = None) -> Iterable[T]:
        pass

    def serialize_codec_data(self, message: Iterable[T]) -> bytes:
        pass
