from collections.abc import Callable, Collection, Iterable
from typing import Generic, Literal, Protocol, TypeVar

import numpy as np
from numpy.linalg import linalg
from statsmodels.regression.linear_model import yule_walker, burg

from prefix_codes.codecs.base import BaseCodec
from prefix_codes.codecs.base import T

I = TypeVar('I', bound=Collection[int])
PredictorType = Callable[[I], int]


class ModelProtocol(Protocol):
    def __call__(self, data: np.ndarray, order: int, **kwargs):
        ...


def attempt(f: Callable, default=0):
    try:
        return f()
    except Exception as e:
        print(str(e), " => fallback to", default)
        return default


def optimal_affine_predictor_statistics(
    source: np.ndarray,
    # Maps current sample index to an already observed sample's index.
    # TODO: Use np.roll https://numpy.org/doc/stable/reference/generated/numpy.roll.html
    correlations: Collection[I],
):
    mean = np.mean(source)
    centered_source = source - mean
    variance = np.var(source)

    # sum_centered = np.sum(centered_source)
    denominator = np.sum(centered_source ** 2)
    print(denominator)

    B_n = np.array([
        np.roll(source, corr)
        for corr in correlations
    ])
    B_n_centered = B_n - mean

    # print(centered_source.shape)
    # print(B_n[0].shape)
    # print(source)
    # print(B_n[0])

    # print(all(
    #     source[y, x] == B_n[0][y, x-1]
    #     for x in range(1, 60)
    #     for y in range(1, 60)
    # ))
    # # print('?', source[0, 1], B_n[0][0, 0])
    # # print('?', source[0, 2], B_n[0][0, 1])
    # # print('?', source[1, 1], B_n[0][1, 0])
    # # print('?', source[1, 2], B_n[0][1, 1])
    # # print('?', source[2, 1], B_n[0][2, 0])
    # # print('?', source[2, 2], B_n[0][2, 1])
    # print((centered_source * B_n[0]).shape)
    # # print(centered_source * B_n[0])
    print(np.sum(centered_source * B_n_centered[0]) / denominator)
    print(np.sum(centered_source * B_n_centered[1]) / denominator)
    print(np.sum(centered_source * B_n_centered[2]) / denominator)

    print('>', np.corrcoef(B_n[0], B_n[0].T))

    C_B = np.zeros(
        (len(correlations), len(correlations))
    )


    # print(np.sum(centered_source * B_n[2]) / denominator)
    # print(np.sum(centered_source * B_n[3]) / denominator)

    print('C_B', np.corrcoef(B_n[0]))

    # print('yw:', yule_walker(source.reshape(-1), order=4))

    # print('B_n', B_n)
    # # auto-covariance matrix / sigma**2
    # C_B = np.corrcoef(B_n)
    # print('C_B', C_B)
    # # cross-covariance vector
    # c = np.array([
    #     (centered_source @ B_n[k]) / variance
    #     for k, observation in enumerate(observations)
    # ])

    return dict(
        mean=mean,
        variance=variance,
        # C_B=C_B,
        # c=c,
    )


def optimal_affine_predictor(
    source: np.ndarray,
    # Maps current sample index to an already observed sample's index.
    # TODO: Use np.roll https://numpy.org/doc/stable/reference/generated/numpy.roll.html
    observations: Collection[Callable[[I], I]],
    model: Literal['burg', 'yule_walker'] = 'yule_walker',
) -> PredictorType:
    """07-PredictiveCoding.pdf, slides 20 - 24"""

    # k = len(observations)
    mean = np.mean(source)
    print('mean:', mean)
    centered_source = source - mean
    print('shape', source.shape)
    print(centered_source)
    variance = np.var(source)
    print(mean, variance)
    # observation set
    B_n = np.array([
        [
            attempt(lambda: source[observation(index)])
            for index in np.ndindex(*source.shape)
        ]
        for observation in observations
    ])
    print('B_n', B_n)
    # auto-covariance matrix / sigma**2
    C_B = np.corrcoef(B_n)
    print('C_B', C_B)
    # cross-covariance vector
    c = np.array([
        (centered_source @ B_n[k]) / variance
        for k, observation in enumerate(observations)
        # np.sum([
        #     centered_source[index] * attempt(centered_source[observation(index)])
        #     for observation in observations
        #     for index in np.ndindex(*source.shape)
        # ])
        # / centered_source2
    ])
    print('------------------------------')
    print('c', c)
    # prediction parameters
    a = linalg.solve(C_B, c)
    print('a =', a)
    constant_offset = mean * (1 - np.sum(a))
    model_instance: ModelProtocol
    match model:
        case 'burg':
            model_instance = burg
        case 'yule_walker':
            model_instance = yule_walker
    print('yw:', yule_walker(source, order=len(observations)))

    def predictor(index: I) -> int:
        return round(
            constant_offset + (
                a @ np.array([
                    attempt(source[observation(index)])
                    for observation in observations
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
