from abc import ABC, abstractclassmethod
from dataclasses import dataclass, field
from typing import Any, Optional, TypeVar, Union, TYPE_CHECKING
from loguru import logger

from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import (
    CLatencyJitterImpairment,
    CDropImpairment,
    CMisorderingImpairment,
    CDuplicationImpairment,
    CCorruptionImpairment,
    CPolicerImpairment,
    CShaperImpairment,
)
from chimera_core.core.manager.__dataset import IterDataclassMixin, GeneratorToken
if TYPE_CHECKING:
    from chimera_core.types.dataset import (
        CustomDistribution
    )



INTERVEL_CHECK_RESERVE_RESOURCE = 0.01
TPLD_FILTERS_LENGTH = 16

TImpairmentGeneral = TypeVar(
    'TImpairmentGeneral',
    CLatencyJitterImpairment,
    CDropImpairment,
    CMisorderingImpairment,
    CLatencyJitterImpairment,
    CPolicerImpairment,
    CDuplicationImpairment,
    CCorruptionImpairment,
    CShaperImpairment,
)

TImpairmentWithDistribution = Union[
    CLatencyJitterImpairment,
    CDropImpairment,
    CMisorderingImpairment,
    CLatencyJitterImpairment,
    CDuplicationImpairment,
    CCorruptionImpairment,
]

class DistributionConfigBase(ABC, IterDataclassMixin):
    def load_token_response_value(self, distribution_token_response: Any) -> None:
        for field in self:
            if hasattr(distribution_token_response, field.name) and (value := getattr(distribution_token_response, field.name)):
                setattr(self, field.name, value)
            # else:
            #     raise ValueError(f'{self} {field_name} could not be None')

    @abstractclassmethod
    def _apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        raise NotImplementedError


@dataclass
class Schedule:
    duration: int
    period: int

    def _apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.schedule.set(duration=self.duration, period=self.period)


class ScheduleMixin:
    schedule: Schedule

    def set_schedule(self, duration: int, period: int) -> None:
        if not hasattr(self, 'schedule'):
            self.schedule = Schedule(duration=duration, period=period)
        else:
            self.schedule.duration = duration
            self.schedule.period = period

@dataclass
class DistributionWithBurstSchedule(DistributionConfigBase, ScheduleMixin):
    schedule: Schedule = field(init=False)

    def one_shot(self) -> None:
        """When started, the impairment will be applied for the duration of the burst. When the burst terminates, the impairment is turned off.
        """
        self.set_schedule(duration=1, period=0)

    def repeat(self, period: int) -> None:
        """When started, the impairment is applied with the configured distribution in a repeated pattern. First it will be applied for a configurable duration and then turned off. It will be restarted for every repeat period.

        :param period: repeat period in ms
        :type period: int
        """
        self.set_schedule(duration=1, period=period)

    def _apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield from self.schedule._apply(impairment)


@dataclass
class DistributionWithFixedContinuousSchedule(DistributionConfigBase):
    def _apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        # fixed value combination represent contiguous in xena server
        yield impairment.schedule.set(duration=1, period=0)


@dataclass
class DistributionWithNonBurstSchedule(DistributionConfigBase, ScheduleMixin):
    schedule: Schedule = field(init=False)

    def continuous(self) -> None:
        """When started, the impairment is applied continuously with the configured distribution until it is manually stopped.
        """
        self.set_schedule(duration=1, period=0)

    def repeat_pattern(self, duration: int, period: int) -> None:
        """When started, the impairment is applied with the configured distribution in a repeated pattern. First it will be applied for a configurable duration and then turned off. It will be restarted for every repeat period.

        :param duration: specifies the "on" period. Units = multiples of 10 ms (range 1 to 65535)
        :type duration: int
        :param period: specifies the "total" period. Units = multiples of 10 ms (range 0 to 65535)
        :type period: int
        """
        self.set_schedule(duration=duration, period=period)

    def _apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield from self.schedule._apply(impairment)


@dataclass
class Step(DistributionWithNonBurstSchedule):
    """The Step Distribution will apply an impairment to a flow, randomly altering between two configurable values. The step distribution is only applicable to latency / jitter.

    :param min: specifies the minimum delay in multiples of 100 ns
    :type min: int
    :param max: specifies the maximum delay in multiples of 100 ns
    :type max: int
    """
    min: int = 0
    """specifies the minimum delay in multiples of 100 ns"""
    max: int = 0
    """specifies the maximum delay in multiples of 100 ns"""

    def _apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.step.set(low=self.min, high=self.max)
        yield from super()._apply(impairment)


@dataclass
class FixedBurst(DistributionWithBurstSchedule):
    """Fixed Burst, when triggered, will impair a number of consecutive packets specified by the Burst Size.

    :param burst_size: burst size in frames
    :type burst_size: int
    """
    burst_size: int = 0
    """burst size in frames"""

    def _apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.fixed_burst.set(burst_size=self.burst_size)
        yield from super()._apply(impairment)


@dataclass
class RandomBurst(DistributionWithNonBurstSchedule):
    """Random Burst implements bursts of random size. The burst is triggered randomly based on a configurable per packet probability and subsequently impair a random number of consecutive packets chosen between minimum burst size (Burst Min) and maximum burst size (Burst Max).

    :param minimum: minimum burst size in frames
    :type minimum: int
    :param maximum: maximum burst size in frames
    :type maximum: int
    :param probability: probability in ppm
    :type probability: int
    """

    minimum: int = 0
    """minimum burst size in frames
    """
    maximum: int = 0
    """maximum burst size in frames
    """
    probability: int = 0
    """probability in ppm
    """

    def _apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.random_burst.set(
            minimum=self.minimum,
            maximum=self.maximum,
            probability=self.probability,
            )
        yield from super()._apply(impairment)


@dataclass
class FixedRate(DistributionWithNonBurstSchedule):
    """Fixed Rate will impair a configurable fraction of the packets in a predictable way, with nearly equal distance between impairments.

    :param probability: probability in ppm
    :type probability: int
    """

    probability: int = 0
    """probability in ppm"""

    def _apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.fixed_rate.set(probability=self.probability)
        yield from super()._apply(impairment)


@dataclass
class GilbertElliot(DistributionWithNonBurstSchedule):
    """The Gilbert-Elliot distribution defines two states, each with a separate packet impairment probability:

    * Good state
    * Bad state

    In any of the two states, there is a certain probability that the system will transition to the other state.

    When the system is in the Good State,there is a configurable impairment probability and there is a configurable probability to transition to the Bad State. Likewise, when in the Bad State, there is a configurable impairment probability and a configurable probability to transition to the Good State.

    :param good_state_impair_prob: a configurable impairment probability in ppm in Good State
    :type good_state_impair_prob: int
    :param good_state_trans_prob: a configurable probability in ppm to transition from Good State to the Bad State
    :type good_state_trans_prob: int
    :param bad_state_impair_prob: a configurable impairment probability in ppm in Bad State
    :type bad_state_impair_prob: int
    :param bad_state_trans_prob: a configurable probability in ppm to transition from Bad State to the Good State
    :type bad_state_trans_prob: int
    """
    good_state_impair_prob: int = 0
    """a configurable impairment probability in ppm in Good State"""
    good_state_trans_prob: int = 0
    """a configurable probability in ppm to transition from Good State to the Bad State"""
    bad_state_impair_prob: int = 0
    """a configurable impairment probability in ppm in Bad State"""
    bad_state_trans_prob: int = 0
    """a configurable probability in ppm to transition from Bad State to the Good State"""

    def _apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.ge.set(
            good_state_prob=self.good_state_impair_prob,
            good_state_trans_prob=self.good_state_trans_prob,
            bad_state_prob=self.bad_state_impair_prob,
            bad_state_trans_prob=self.bad_state_trans_prob,
        )
        yield from super()._apply(impairment)


@dataclass
class Uniform(DistributionWithNonBurstSchedule):
    """The Uniform Distribution will randomly select the distance between impairments from a configured interval defined by a minimum and a maximum value.

    :param minimum: specifies the minimum number of packets or multiples of 100 ns in case of latency for the uniform distribution
    :type minimum: int
    :param maximum: specifies the maximum number of packets or multiples of 100 ns in case of latency for the uniform distribution
    :type maximum: int
    """
    minimum: int = 0
    """specifies the minimum number of packets or multiples of 100 ns in case of latency for the uniform distribution"""
    maximum: int = 0
    """specifies the maximum number of packets or multiples of 100 ns in case of latency for the uniform distribution"""

    def _apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.uniform.set(
            minimum=self.minimum,
            maximum=self.maximum,
        )
        yield from super()._apply(impairment)


@dataclass
class Gaussian(DistributionWithNonBurstSchedule):
    """The Gaussian (Normal) distribution implements an approximation of the mathematical function, which is defined by a mean value (μ) and a standard deviation (σ). When a flow is configured for Gaussian Jitter, the mean latency of packets is equal to the configured mean latency, and the deviations of single packets from the mean will be according to the Gaussian distribution.

    Chimera limits the Gaussian function to the following latency interval:

    μ - 3 x σ <= simulated values <= μ + 3 x σ

    :param mean: specifies the mean value of packets or multiples of 100 ns in case of latency for the Gaussian distribution
    :type mean: int
    :param sd: specifies the standard deviation value of packets or multiples of 100 ns in case of latency for the Gaussian distribution
    :type sd: int
    """
    mean: int = 0
    """specifies the mean value of packets or multiples of 100 ns in case of latency for the Gaussian distribution"""
    sd: int = 0
    """specifies the standard deviation value of packets or multiples of 100 ns in case of latency for the Gaussian distribution"""

    def _apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.gaussian.set(
            mean=self.mean,
            std_deviation=self.sd,
        )
        yield from super()._apply(impairment)


@dataclass
class Gamma(DistributionWithNonBurstSchedule):
    """The Gamma distribution approximates the mathematical function which is defined by a Shape parameter (κ) and the Scale parameter (θ). The Gamma distribution is illustrated in Figure 60 for different values of the Shape and Scale parameters. When a flow is configured for Gamma Latency / Jitter, the mean latency of packets is equal to the configured mean latency, and the deviations of single packets from the mean will be according to the Gamma distribution.

    Chimera limits the Gamma function to the following latency interval:

    μ - 4 x σ <= simulated values <= μ + 4 x σ

    where,
    σ = sqrt(κ * θ^2) (standard deviation)
    μ = κ∗θ (mean value)

    :param shape: gamma distribution Shape parameter
    :type shape: int
    :param scale: gamma distribution Scale parameter
    :type scale: int
    """
    shape: int = 0
    """gamma distribution Shape parameter"""
    scale: int = 0
    """gamma distribution Scale parameter"""

    def _apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.gamma.set(
            shape=self.shape,
            scale=self.scale,
        )
        yield from super()._apply(impairment)


@dataclass
class Poisson(DistributionWithNonBurstSchedule):
    """The Poisson distribution approximates the mathematical function which is defined by a mean value (λ). When a flow is configured for poisson jitter, the mean latency of packets is equal to the configured mean latency, and the deviations of single packets from the mean will be according to the Poisson distribution.

    Chimera limits the Poisson function to the following latency interval:

    μ - 3 x σ <= simulated values <= μ + 3 x σ

    where,
    σ = sqrt(λ) (standard deviation)
    μ = λ (Mean value)

    :param lamda: Specifies the mean value for the Poisson distribution
    :type lamda: int
    """

    lamda: int = 0
    """Specifies the lamda value for the Poisson distribution"""

    def _apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.poisson.set(mean=self.lamda)
        yield from super()._apply(impairment)


@dataclass
class Custom(DistributionWithNonBurstSchedule):
    """In addition to the pre-defined distributions described above, Chimera supports the definition of Custom Distributions. Custom distributions are table-based distributions which are defined per port. They are identified by a Custom ID (cust_id), which identifies each custom distribution on that port. Chimera supports up to 40 custom distributions per port (cust_id: 1-40). Once the custom distribution is defined, it can be applied to any of the impairments in the impairment pipeline.

    A custom distribution is a table-based distribution, where the user can supply the values in the table. Furthermore, the user can configure whether the values in the table should be applied in a predictable order, reading out table index 0, 1, 2 … 511/1023 -> 0, 1, 2 …, or whether the values are applied in a random order.

    Finally, the user can supply a Custom Name for every custom distribution to make it easier to navigate within the distributions defined.

    The custom distributions will support 512 table entries for inter-packet distributions and 1024 values for latency / jitter distributions. As a result, only custom distributions with 1024 entries may be assigned to latency / jitter, while custom distributions with 512 entries can be assigned to all other impairments except for misordering, which does not support custom distributions.

    :param custom_distribution: specifies the customer distribution object
    :type custom_distribution: CustomDistribution
    :param cust_id: specifies the customer distribution index
    :type cust_id: int
    """
    custom_distribution: Optional["CustomDistribution"] = None
    """specifies the customer distribution object"""
    cust_id: Optional[int] = None
    """specifies the customer distribution index"""

    def _apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        cust_id = self.custom_distribution.custom_distribution_index if self.custom_distribution else self.cust_id
        assert cust_id
        yield impairment.distribution.custom.set(cust_id=cust_id)
        yield from super()._apply(impairment)


@dataclass
class AccumulateBurst(DistributionWithBurstSchedule):
    """Chimera allows simulating temporary congestion in a network using the Accumulate and Burst distribution. For a configurable period (Burst Delay), packets are collected in a buffer, rather than forwarded to the output port. After this period of time, all the buffered packets are forwarded to the output as fast as possible, thus creating a burst. Once buffered packets have been transmitted from the buffer, packets will be forwarded with minimum latency.

    The packet accumulation is triggered by the first packet received on the flow after the distribution was enabled.

    :param burst_delay: specifies the duration of the packet accumulation after receiving the first packet in multiples of 100 ns.
    :type burst_delay: int
    """
    burst_delay: int = 0
    """specifies the duration of the packet accumulation after receiving the first packet in multiples of 100 ns"""

    def _apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.accumulate_and_burst.set(delay=self.burst_delay)
        yield from super()._apply(impairment)


@dataclass
class BitErrorRate(DistributionWithNonBurstSchedule):
    """Bit Error Rate will impair the packets of a flow equivalent to a configured BER. For instance, if configured for a BER of 5*10-8, an impairment will be applied for every 0.2*108 bits on the flow. The impairments are applied in a predictable way, with nearly equal distance between impairments.

    BER = coefficient * 10^exponent

    :param coefficient: the mantissa of the configured BER
    :type coefficient: int
    :param exponent: the exponent of the configured BER
    :type exponent: int
    """
    coefficient: int = 0
    """the mantissa of the configured BER"""
    exponent: int = 0
    """the exponent of the configured BER"""

    def _apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.bit_error_rate.set(coef=self.coefficient, exp=self.exponent)
        yield from super()._apply(impairment)


@dataclass
class RandomRate(DistributionWithNonBurstSchedule):
    """Random Rate will impair a configurable fraction of the packets based on a per packet drop probability, i.e. unlike fixed rate, the impairment pattern is stochastic with an average equal to the configured Impair Probability.

    :param probability: fraction of packets to impair in ppm
    :type probability: int
    """
    probability: int = 0
    """fraction of packets to impair in ppm"""

    def _apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.random_rate.set(probability=self.probability)
        yield from super()._apply(impairment)


@dataclass
class ConstantDelay(DistributionWithFixedContinuousSchedule):
    """“Constant Delay will apply a constant delay to all packets in the flow.

    :param DistributionWithFixedContinuousSchedule: _description_
    :type DistributionWithFixedContinuousSchedule: _type_
    :yield: _description_
    :rtype: _type_
    """
    delay: int = 0

    def _apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.distribution.constant_delay.set(delay=self.delay)
        yield from super()._apply(impairment)
