from abc import ABC, abstractmethod
from collections.abc import Hashable, Iterable
from typing import TypeVar, Generic

T = TypeVar('T', bound=Hashable)


class BaseCodec(ABC, Generic[T]):

    @classmethod
    @abstractmethod
    def deserialize(cls, serialization: bytes) -> 'BaseCodec[T]':
        ...

    @abstractmethod
    def encode(self, message: Iterable[T]) -> bytes:
        ...

    @abstractmethod
    def decode(self, byte_stream: bytes, *, max_length: int = None) -> Iterable[T]:
        ...

    @abstractmethod
    def serialize(self) -> bytes:
        ...


# class ArithmeticCodec(BaseCodec, Generic[T]):
