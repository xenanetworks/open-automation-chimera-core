from abc import ABC, abstractclassmethod
from dataclasses import dataclass, field
from typing import Any, TypeVar

from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import (
    CLatencyJitterImpairment,
    CDropImpairment,
    CMisorderingImpairment,
    CDuplicationImpairment,
    CCorruptionImpairment,
)
from chimera_core.core.manager.__dataset import IterDataclassMixin, GeneratorToken



INTERVEL_CHECK_RESERVE_RESOURCE = 0.01
TPLD_FILTERS_LENGTH = 16


TImpairmentWithDistribution = TypeVar(
    'TImpairmentWithDistribution',
    CLatencyJitterImpairment,
    CDropImpairment,
    CMisorderingImpairment,
    CLatencyJitterImpairment,
    CDuplicationImpairment,
    CCorruptionImpairment,
)

class DistributionConfigBase(ABC, IterDataclassMixin):
    def load_token_response_value(self, distribution_token_response: Any) -> None:
        for field in self:
            if hasattr(distribution_token_response, field.name) and (value := getattr(distribution_token_response, field.name)):
                setattr(self, field.name, value)
            # else:
            #     raise ValueError(f'{self} {field_name} could not be None')

    @abstractclassmethod
    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        raise NotImplementedError


@dataclass
class Schedule:
    duration: int = 0
    period: int = 0

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
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

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield from self.schedule.apply(impairment)


@dataclass
class DistributionWithFixedContinuousSchedule(DistributionConfigBase):
    schedule: Schedule = field(default_factory=lambda: Schedule(duration=1, period=0))

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
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

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield from self.schedule.apply(impairment)


@dataclass
class Step(DistributionWithBurstSchedule):
    low: int = 0
    high: int = 0

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.step.set(low=self.low, high=self.high)
        yield from super().apply(impairment)


@dataclass
class FixedBurst(DistributionWithBurstSchedule):
    burst_size: int = 0

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.fixed_burst.set(burst_size=self.burst_size)
        yield from super().apply(impairment)


@dataclass
class RandomBurst(DistributionWithNonBurstSchedule):
    minimum: int = 0
    maximum: int = 0
    probability: int = 0

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.random_burst.set(
            minimum=self.minimum,
            maximum=self.maximum,
            probability=self.probability,
            )
        yield from super().apply(impairment)


@dataclass
class FixedRate(DistributionWithNonBurstSchedule):
    probability: int = 0

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.fixed_rate.set(probability=self.probability)
        yield from super().apply(impairment)


@dataclass
class GilbertElliot(DistributionWithNonBurstSchedule):
    good_state_prob: int = 0
    good_state_trans_prob: int = 0
    bad_state_prob: int = 0
    bad_state_trans_prob: int = 0

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
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

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.uniform.set(
            minimum=self.minimum,
            maximum=self.maximum,
        )
        yield from super().apply(impairment)


@dataclass
class Gaussian(DistributionWithNonBurstSchedule):
    mean: int = 0
    std_deviation: int = 0

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.gaussian.set(
            mean=self.mean,
            std_deviation=self.std_deviation,
        )
        yield from super().apply(impairment)


@dataclass
class Gamma(DistributionWithNonBurstSchedule):
    shape: int = 0
    scale: int = 0

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.gamma.set(
            shape=self.shape,
            scale=self.scale,
        )
        yield from super().apply(impairment)


@dataclass
class Poisson(DistributionWithNonBurstSchedule):
    mean: int = 0

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.poisson.set(mean=self.mean)
        yield from super().apply(impairment)


@dataclass
class Custom(DistributionWithNonBurstSchedule):
    cust_id: int = 0

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.custom.set(cust_id=self.cust_id)
        yield from super().apply(impairment)


@dataclass
class AccumulateBurst(DistributionWithBurstSchedule):
    delay: int = 0

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.accumulate_and_burst.set(delay=self.delay)
        yield from super().apply(impairment)


@dataclass
class BitErrorRate(DistributionWithNonBurstSchedule):
    coef: int = 0
    exp: int = 0

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.bit_error_rate.set(coef=self.coef, exp=self.exp)
        yield from super().apply(impairment)


@dataclass
class RandomRate(DistributionWithNonBurstSchedule):
    probability: int = 0

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.random_rate.set(probability=self.probability)
        yield from super().apply(impairment)


@dataclass
class ConstantDelay(DistributionWithFixedContinuousSchedule):
    delay: int = 0

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        # yield impairment.distribution.constant_delay.set(delay=self.delay)
        yield from super().apply(impairment)
