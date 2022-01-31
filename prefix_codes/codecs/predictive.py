import pickle
from abc import abstractmethod
from collections import OrderedDict
from collections.abc import Callable, Collection, Iterable
from collections.abc import Iterator
from typing import TypeVar, Protocol, ParamSpec, Concatenate

import numpy as np
import numpy.typing as npt
from numpy.linalg import linalg

from prefix_codes.codecs.rice import RiceCodec
from prefix_codes.codecs.arithmetic import ArithmeticAdaptivePmfCodec
from prefix_codes.codecs.base import BaseCodec
from prefix_codes.codecs.base import T
from prefix_codes.utils import get_relative_frequencies

I = TypeVar('I', bound=Collection[int])
P = ParamSpec('P')

PredictorType = Callable[[I, Iterable[T]], int]
PredictorFactory = Callable[Concatenate[Iterable[T], P], PredictorType]


def optimal_affine_predictor_params(
    source: np.ndarray,
    # Specifies the observed samples' indices relative from the current sample's index.
    observations: Collection[I],
) -> dict[str, np.ndarray | float | int]:
    mean = np.mean(source)
    variance = np.var(source)

    B_n = np.array([
        np.roll(source, observation_index)
        for observation_index in observations
    ])

    # auto-covariance matrix / sigma**2
    C_B = np.corrcoef(B_n)
    # print('C_B', C_B)

    # cross-covariance vector
    c = np.corrcoef(source, B_n)[0, 1:]  # use 1st row's entries except 1
    # print('c', c)

    # prediction parameters
    a = linalg.solve(C_B, c)
    # print('a', a)

    a0 = mean * (1 - np.sum(a))

    return dict(
        mean=mean,
        variance=variance,
        B_n=B_n,
        C_B=C_B,
        c=c,
        a=a,
        a0=a0,
    )


def optimal_affine_predictor_factory(
    source: np.ndarray,
    # Maps current sample index to an already observed sample's index.
    # TODO: Use np.roll https://numpy.org/doc/stable/reference/generated/numpy.roll.html
    observations: Collection[I],
) -> PredictorType:
    """07-PredictiveCoding.pdf, slides 20 - 24"""

    params = optimal_affine_predictor_params(source, observations)
    offset: float = params['a0']
    prediction_params: np.ndarray = params['a']
    observation_sets: np.ndarray = params['B_n']

    def predictor(index: I, source: Iterable[T]) -> int:
        return round(
            offset + (
                prediction_params @ np.array([
                    observation_set[index]
                    for observation_set in observation_sets
                ])
            )
        )
    return predictor


def left_and_above_avg_predictor(index: I, source: npt.NDArray[int]) -> int:
    """Assume source.shape == (height, width)."""

    assert source.dtype == int, f'expected source of integers but got {source.dtype}\n{source}'

    y, x = index
    left: int
    above: int
    try:
        left = source[y, x - 1]
    except IndexError:
        left = 0
    try:
        above = source[y - 1, x]
    except IndexError:
        above = 0

    return (left + above) // 2


###############################################################################


class SubtractableIterable(Protocol[T]):
    def __sub__(self, other) -> Iterable[T]:
        ...

    def __iter__(self) -> Iterator[T]:
        ...


S = TypeVar('S', bound=SubtractableIterable)


class PredictiveCodec(BaseCodec[S]):
    predictor: PredictorType
    # codec: BaseCodec

    # def __init__(self, predictor: PredictorType, prediction_error_codec: BaseCodec):
    def __init__(self, predictor: PredictorType):
        self.predictor = predictor
        # self.codec = prediction_error_codec

    # @classmethod
    # def decode_byte_stream(cls, serialization: bytes) -> S:
    #     ...

    def encode(self, message: S, *, max_length: int = None) -> bytes:
        return self.encode_prediction_errors(
            self.get_predictions_errors(message),
            max_length,
        )

    def get_predictions(self, message: S) -> npt.NDArray[T]:
        return np.array([self.predictor(index, message) for index in self.iter_index(message)])

    def iter_index(self, message: S) -> Iterable[tuple[int, ...]]:
        return ((i,) for i in message)

    def get_predictions_errors(self, message: S) -> npt.NDArray[T]:
        return message - self.get_predictions(message)

    @abstractmethod
    def encode_prediction_errors(self, prediction_errors: S, max_length: int = None) -> bytes:
        ...

    def decode(self, byte_stream: bytes, *, max_length: int = None, **kwargs) -> S:
        prediction_errors = self.decode_prediction_errors(
            byte_stream,
            max_length,
            **kwargs,
        )
        return self.reconstructed(prediction_errors)

    @abstractmethod
    def decode_prediction_errors(self, byte_stream: bytes, max_length: int = None, **kwargs) -> S:
        ...

    @abstractmethod
    def reconstructed(self, prediction_errors: S) -> S:
        ...


class PredictiveImageCodec(PredictiveCodec[npt.NDArray[int]]):
    codec = RiceCodec(R=4, alphabet=list(range(-255, 256)))
    width: int
    height: int

    def __init__(self, predictor: PredictorType, width: int, height: int):
        super().__init__(predictor)
        self.width = width
        self.height = height

    @classmethod
    def decode_byte_stream(cls, serialization: bytes) -> S:
        predictor: PredictorType
        width: int
        height: int
        probabilities: OrderedDict[T, float]

        codec_data, enc_message, message_length = cls.parse_byte_stream(serialization)
        predictor, width, height, relative_frequencies = pickle.loads(codec_data)
        codec = cls(predictor, width, height)
        return codec.decode(enc_message, max_length=message_length, probabilities=relative_frequencies)

    def get_message_length(self, message: S) -> int:
        assert message.shape == (self.height, self.width), 'invalid dimensions'
        return self.width * self.height

    def serialize_codec_data(self, message: npt.NDArray[int]) -> bytes:
        # relative_frequencies: dict[int, float] = get_relative_frequencies(self.get_predictions_errors(message).reshape(-1))
        # return pickle.dumps([self.predictor, self.width, self.height, relative_frequencies])
        return pickle.dumps([self.predictor, self.width, self.height])

    def encode_prediction_errors(self, prediction_errors: npt.NDArray[int], max_length: int = None) -> bytes:
        relative_frequencies: dict[int, float] = get_relative_frequencies(prediction_errors.reshape(-1))
        # codec = ArithmeticAdaptivePmfCodec(
        #     V=24,
        #     U=24,
        #     probabilities=OrderedDict(relative_frequencies),
        #     prefix_free=False,
        # )
        # codec = RiceCodec(R=4, alphabet=list(range(-255, 256)))
        return self.codec.encode(prediction_errors.reshape(-1), max_length=max_length)

    def get_predictions(self, message: npt.NDArray[int]) -> npt.NDArray[int]:
        return super().get_predictions(message).reshape((self.height, self.width))

    def iter_index(self, message: npt.NDArray[int]) -> Iterable[tuple[int, ...]]:
        return np.ndindex(*message.shape)

    # def decode_prediction_errors(self, byte_stream: bytes, max_length: int = None, probabilities: dict[int, float] = None, **kwargs) -> npt.NDArray[int]:
    #     assert probabilities is not None, 'no probabilities for arithmetic (non-adaptive) decoding'
    #     codec = ArithmeticAdaptivePmfCodec(
    #         V=24,
    #         U=24,
    #         probabilities=OrderedDict(probabilities),
    #         prefix_free=False,
    #     )
    #     return np.array(list(codec.decode(byte_stream, max_length=max_length))).reshape(self.height, self.width)
    def decode_prediction_errors(self, byte_stream: bytes, max_length: int = None, **kwargs) -> npt.NDArray[int]:
        # codec = RiceCodec(R=4, alphabet=list(range(-255, 256)))
        return np.array(list(
            self.codec.decode(byte_stream, max_length=max_length)
        )).reshape(self.height, self.width)

    def reconstructed(self, prediction_errors: npt.NDArray[int]) -> npt.NDArray[int]:
        print('reconstructing from prediction_errors')
        print(prediction_errors)
        # get_predictions with iteratively filling message
        original: npt.NDArray[int] = np.zeros(prediction_errors.shape, dtype=int)
        for index in self.iter_index(prediction_errors):
            # print('idx', index)
            original[index] = self.predictor(index, original) + prediction_errors[index]  # type: ignore
        print('reconstructed', original)
        return original

