from collections.abc import Callable, Collection, Iterable
from collections.abc import Iterator
from typing import TypeVar, Protocol, ParamSpec, Concatenate

import numpy as np
import numpy.typing as npt
from numpy.linalg import linalg

from prefix_codes.codecs.base import BaseCodec
from prefix_codes.codecs.base import T

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

    assert source.dtype == int, f'expected source of integers but got {source.dtype}'

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
    codec: BaseCodec

    def __init__(self, predictor: PredictorType, prediction_error_codec: BaseCodec):
        self.predictor = predictor
        self.codec = prediction_error_codec

    # @classmethod
    # def decode_byte_stream(cls, serialization: bytes) -> Iterable[T]:
    #     ...

    def encode(self, message: S, *, max_length: int = None) -> bytes:
        return self.encode_prediction_errors(
            self.get_predictions_errors(message, self.get_predictions(message)),
            max_length,
        )

    def get_predictions(self, message: S) -> S:
        return np.array(self.predictor(sample) for sample in message)

    def get_predictions_errors(self, message: S, predictions: S) -> S:
        return message - predictions

    def encode_prediction_errors(self, prediction_errors: S, max_length: int = None) -> bytes:
        return self.codec.encode(prediction_errors, max_length=max_length)

    def decode(self, byte_stream: bytes, *, max_length: int = None) -> Iterable[T]:
        pass

    # def serialize_codec_data(self, message: Iterable[T]) -> bytes:
    #     ...


class PredictiveImageCodec(PredictiveCodec[npt.NDArray[int]]):
    ...
