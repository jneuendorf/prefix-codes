from abc import ABC, abstractmethod
from collections.abc import Hashable, Iterable
from math import ceil
from typing import TypeVar, Generic

T = TypeVar('T', bound=Hashable)

META_BYTES = 30


# TODO: replace Iterable[T] with T so that subclasses can specify other container types such as numpy arrays
class BaseCodec(ABC, Generic[T]):

    @staticmethod
    def parse_byte_stream(serialization: bytes) -> tuple[bytes, bytes, int]:
        meta = serialization[:META_BYTES]
        codec_data_and_message = serialization[META_BYTES:]

        num_codec_data_bytes = int.from_bytes(meta[:META_BYTES // 2], byteorder='big')
        message_length = int.from_bytes(meta[META_BYTES // 2:], byteorder='big')

        codec_data = codec_data_and_message[:num_codec_data_bytes]
        enc_message = codec_data_and_message[num_codec_data_bytes:]
        return codec_data, enc_message, message_length

    @classmethod
    @abstractmethod
    def decode_byte_stream(cls, serialization: bytes) -> Iterable[T]:
        ...

    @abstractmethod
    def encode(self, message: Iterable[T], *, max_length: int = None) -> bytes:
        ...

    @abstractmethod
    def decode(self, byte_stream: bytes, *, max_length: int = None) -> Iterable[T]:
        ...

    def serialize(self, message: Iterable[T]) -> bytes:
        codec_data = self.serialize_codec_data(message)
        message_length = self.get_message_length(message)
        assert ceil(len(codec_data).bit_length() / 8) <= META_BYTES // 2, (
            f'codec data is too large'
        )
        assert ceil(message_length.bit_length() / 8) <= META_BYTES // 2, (
            f'message is too large'
        )
        return (
            len(codec_data).to_bytes(length=META_BYTES // 2, byteorder='big')
            + message_length.to_bytes(length=META_BYTES // 2, byteorder='big')
            + codec_data
            + self.encode(message)
        )

    def get_message_length(self, message: Iterable[T]) -> int:
        return len(list(message))

    @abstractmethod
    def serialize_codec_data(self, message: Iterable[T]) -> bytes:
        ...
