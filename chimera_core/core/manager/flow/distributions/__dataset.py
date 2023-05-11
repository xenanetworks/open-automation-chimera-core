import ipaddress
from dataclasses import dataclass, field, fields
from typing import Any, Callable, Coroutine, Dict, Generator, Generic, List, NamedTuple, Optional, Protocol, Tuple, Type, TypeVar, Union, cast

from xoa_driver.v2 import misc
from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import (
    CLatencyJitterImpairment,
    CDropImpairment,
    CMisorderingImpairment,
)


INTERVEL_CHECK_RESERVE_RESOURCE = 0.01
TPLD_FILTERS_LENGTH = 16

GeneratorToken = Generator[misc.Token, None, None]



TypeExceptionAny = Union[Exception, Any, None]


TImpairment = Union[
    CDropImpairment,
    CLatencyJitterImpairment,
    CMisorderingImpairment,
]

@dataclass
class DistributionConfigBase:
    def __iter__(self):
        return iter(fields(self))

    def load_server_value(self, distribution_token_response: Any) -> None:
        for field in self:
            if hasattr(distribution_token_response, field.name) and (value := getattr(distribution_token_response, field.name)):
                setattr(self, field.name, value)
            # else:
            #     raise ValueError(f'{self} {field_name} could not be None')

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        raise NotImplementedError


@dataclass
class Schedule:
    duration: int = 0
    period: int = 0

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield impairment.schedule.set(duration=self.duration, period=self.period)


@dataclass
class DistributionWithBurstSchedule(DistributionConfigBase):
    schedule: Schedule = field(default_factory=Schedule)

    def one_shot(self) -> None:
        self.schedule.duration = 1
        self.schedule.period = 0

    def repeat(self, period: int) -> None:
        self.schedule.duration = 1
        self.schedule.period = period

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield from self.schedule.apply(impairment)


@dataclass
class DistributionWithFixedContinuousSchedule(DistributionConfigBase):
    schedule: Schedule = field(default_factory=lambda: Schedule(duration=1, period=0))

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield from self.schedule.apply(impairment)


@dataclass
class DistributionWithNonBurstSchedule(DistributionConfigBase):
    schedule: Schedule = field(default_factory=Schedule)

    def continuous(self) -> None:
        self.duration = 1
        self.period = 0

    def repeat_pattern(self, duration: int, period: int) -> None:
        self.duration = duration
        self.period = period

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield from self.schedule.apply(impairment)


@dataclass
class Step(DistributionWithBurstSchedule):
    low: int = 0
    high: int = 0

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield impairment.distribution.step.set(low=self.low, high=self.high)
        yield from super().apply(impairment)


@dataclass
class FixedBurst(DistributionWithBurstSchedule):
    burst_size: int = 0

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield impairment.distribution.fixed_burst.set(burst_size=self.burst_size)
        yield from super().apply(impairment)


@dataclass
class RandomBurst(DistributionWithNonBurstSchedule):
    minimum: int = 0
    maximum: int = 0
    probability: int = 0

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield impairment.distribution.random_burst.set(
            minimum=self.minimum,
            maximum=self.maximum,
            probability=self.probability,
            )
        yield from super().apply(impairment)


@dataclass
class FixedRate(DistributionWithNonBurstSchedule):
    probability: int = 0

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield impairment.distribution.fixed_rate.set(probability=self.probability)
        yield from super().apply(impairment)


@dataclass
class GilbertElliot(DistributionWithNonBurstSchedule):
    good_state_prob: int = 0
    good_state_trans_prob: int = 0
    bad_state_prob: int = 0
    bad_state_trans_prob: int = 0

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield impairment.distribution.ge.set(
           good_state_prob=self.good_state_prob,
            good_state_trans_prob=self.good_state_trans_prob,
            bad_state_prob=self.bad_state_prob,
            bad_state_trans_prob=self.bad_state_trans_prob,
        )
        yield from super().apply(impairment)


@dataclass
class Uniform(DistributionWithNonBurstSchedule):
    minimum: int = 0
    maximum: int = 0

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield impairment.distribution.uniform.set(
            minimum=self.minimum,
            maximum=self.maximum,
        )
        yield from super().apply(impairment)


@dataclass
class Gaussian(DistributionWithNonBurstSchedule):
    mean: int = 0
    std_deviation: int = 0

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield impairment.distribution.gaussian.set(
            mean=self.mean,
            std_deviation=self.std_deviation,
        )
        yield from super().apply(impairment)


@dataclass
class Gamma(DistributionWithNonBurstSchedule):
    shape: int = 0
    scale: int = 0

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield impairment.distribution.gamma.set(
            shape=self.shape,
            scale=self.scale,
        )
        yield from super().apply(impairment)


@dataclass
class Poisson(DistributionWithNonBurstSchedule):
    mean: int = 0

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield impairment.distribution.poisson.set(mean=self.mean)
        yield from super().apply(impairment)


@dataclass
class Custom(DistributionWithNonBurstSchedule):
    cust_id: int = 0

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield impairment.distribution.custom.set(cust_id=self.cust_id)
        yield from super().apply(impairment)


@dataclass
class AccumulateBurst(DistributionWithBurstSchedule):
    delay: int = 0

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield impairment.distribution.accumulate_and_burst.set(delay=self.delay)
        yield from super().apply(impairment)


@dataclass
class BitErrorRate(DistributionWithNonBurstSchedule):
    coef: int = 0
    exp: int = 0

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield impairment.distribution.bit_error_rate.set(coef=self.coef, exp=self.exp)
        yield from super().apply(impairment)


@dataclass
class RandomRate(DistributionWithNonBurstSchedule):
    probability: int = 0

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield impairment.distribution.random_rate.set(probability=self.probability)
        yield from super().apply(impairment)


@dataclass
class ConstantDelay(DistributionWithFixedContinuousSchedule):
    delay: int = 0

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield impairment.distribution.constant_delay.set(delay=self.delay)
        yield from super().apply(impairment)


class DistributionResponseValidator(NamedTuple):
    """If get command return NOTVALID, the config was not being set"""
    fixed_burst: TypeExceptionAny = None
    random_burst: TypeExceptionAny = None
    fixed_rate: TypeExceptionAny = None
    random_rate: TypeExceptionAny = None
    bit_error_rate: TypeExceptionAny = None
    ge: TypeExceptionAny = None
    uniform: TypeExceptionAny = None
    gaussian: TypeExceptionAny = None
    gamma: TypeExceptionAny = None
    poisson: TypeExceptionAny = None
    custom: TypeExceptionAny = None
    accumulate_and_burst: TypeExceptionAny = None
    constant_delay: TypeExceptionAny = None
    step: TypeExceptionAny = None

    @property
    def valid_distribution_response(self) -> Generator[Tuple[str, Any], None, None]:
        """if token respsonse is not NOTVALID means it was set"""
        for command_name in self._fields:
            if (command_response := getattr(self, command_name)) and not isinstance(command_response, Exception):
                yield command_name, command_response


distribution_class: Dict[str, Type[DistributionConfigBase]] = {
    'fixed_burst': FixedBurst,
    'random_burst': RandomBurst,
    'fixed_rate': FixedRate,
    'random_rate': RandomRate,
    'bit_error_rate': BitErrorRate,
    'gilbert_elliot': GilbertElliot,
    'uniform': Uniform,
    'gaussian': Gaussian,
    'poisson': Poisson,
    'gamma': Gamma,
    'custom': Custom,
    'accumulate_and_burst': AccumulateBurst,
    'constant_delay': ConstantDelay,
}