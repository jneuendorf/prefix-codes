from collections.abc import Callable, Collection, Iterable
from typing import Generic, TypeVar

import numpy as np
from numpy.linalg import linalg

from prefix_codes.codecs.base import BaseCodec
from prefix_codes.codecs.base import T

I = TypeVar('I', bound=Collection[int])
PredictorType = Callable[[I], int]


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


def optimal_affine_predictor(
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

    def predictor(index: I) -> int:
        return round(
            offset + (
                prediction_params @ np.array([
                    observation_set[index]
                    for observation_set in observation_sets
                ])
            )
        )
    return predictor


class PredictiveCodec(BaseCodec, Generic[T]):
    predictor: PredictorType

    def __init__(self, predictor: PredictorType):
        self.predictor = predictor

    # @classmethod
    # def decode_byte_stream(cls, serialization: bytes) -> Iterable[T]:
    #     ...

    def encode(self, message: Iterable[T], *, max_length: int = None) -> bytes:
        pass

    def decode(self, byte_stream: bytes, *, max_length: int = None) -> Iterable[T]:
        pass

    # def serialize_codec_data(self, message: Iterable[T]) -> bytes:
    #     ...
