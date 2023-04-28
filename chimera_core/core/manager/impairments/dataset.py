from collections import namedtuple
from dataclasses import dataclass, field, fields
from typing import Any, Dict, Generator, NamedTuple, Optional, Tuple, Type, Union

from loguru import logger

from xoa_driver import enums
from xoa_driver.v2 import misc
from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import (
    CLatencyJitterImpairment,
    CDropImpairment,
    CMisorderingImpairment,
    CShaperImpairment,
)

from chimera_core.core.manager.distributions.__dataset import (
    FixedBurst,
    RandomBurst,
    FixedRate,
    BitErrorRate,
    RandomRate,
    Gamma,
    Gaussian,
    Uniform,
    Poisson,
    GilbertElliot,
    Custom,
    AccumulateBurst,
    ConstantDelay,
)

TImpairment = Union[
    CDropImpairment,
    CLatencyJitterImpairment,
    CMisorderingImpairment,
]

TypeTokenResponseOrError = Union[Exception, Any]
GeneratorToken = Generator[misc.Token, None, None]


@dataclass
class SupportedDistribution:
    fixed_burst: bool = False
    random_burst: bool = False
    fixed_rate: bool = False
    random_rate: bool = False
    bit_error_rate: bool = False
    ge: bool = False
    uniform: bool = False
    gaussian: bool = False
    gamma: bool = False
    poisson: bool = False
    custom: bool = False
    accumulate_and_burst: bool = False
    constant_delay: bool = False
    step: bool = False

    def __iter__(self):
        return iter(fields(self))


distribution_class: Dict[str, Type[Any]] = {
    'fixed_burst': FixedBurst,
    'random_burst': RandomBurst,
    'fixed_rate': FixedRate,
    'random_rate': RandomRate,
    'bit_error_rate': BitErrorRate,
    'ge': GilbertElliot,
    'uniform': Uniform,
    'gaussian': Gaussian,
    'poisson': Poisson,
    'gamma': Gamma,
    'custom': Custom,
    'accumulate_and_burst': AccumulateBurst,
    'constant_delay': ConstantDelay,
}

class DistributionResponseValidator(NamedTuple):
    """If get command return NOTVALID, the config was not being set"""
    fixed_burst: TypeTokenResponseOrError = None
    random_burst: TypeTokenResponseOrError = None
    fixed_rate: TypeTokenResponseOrError = None
    random_rate: TypeTokenResponseOrError = None
    bit_error_rate: TypeTokenResponseOrError = None
    ge: TypeTokenResponseOrError = None
    uniform: TypeTokenResponseOrError = None
    gaussian: TypeTokenResponseOrError = None
    gamma: TypeTokenResponseOrError = None
    poisson: TypeTokenResponseOrError = None
    custom: TypeTokenResponseOrError = None
    accumulate_and_burst: TypeTokenResponseOrError = None
    constant_delay: TypeTokenResponseOrError = None
    step: TypeTokenResponseOrError = None

    @property
    def filter_valid_distribution(self) -> Generator[Tuple[str, Any], None, None]:
        """if token respsonse is not NOTVALID means it was set"""
        for command_name in self._fields:
            if (command_response := getattr(self, command_name)) and not isinstance(command_response, Exception):
                logger.debug(command_name)
                logger.debug(command_response)
                yield command_name, command_response


@dataclass
class ImpairmentConfigBase:
    enable: enums.OnOff = enums.OnOff.OFF


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
class DistributionManager:
    _current: Optional[DistributionConfigBase] = None

    def get_current_distribution(self) -> Optional["DistributionConfigBase"]:
        return self._current

    def set_distribution(self, distribution: "DistributionConfigBase") -> None:
        self._current = distribution

    def load_value_from_server_response(self, validator: DistributionResponseValidator) -> None:
        for distribution_name, distribution_response in validator.filter_valid_distribution:
            distribution_config = distribution_class[distribution_name]()
            distribution_config.load_server_value(distribution_response)
            self.set_distribution(distribution_config)

    def set_schedule(self, schedule_respsonse: Any) -> None:
        if (distribution := self.get_current_distribution()) \
            and isinstance(distribution, DistributionWithNonBurstSchedule) \
                and not isinstance(schedule_respsonse, Exception):
            distribution.schedule.duration = schedule_respsonse.duration
            distribution.schedule.period = schedule_respsonse.period

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        assert self._current
        yield from self._current.apply(impairment)


@dataclass
class ImpairmentWithDistribution(ImpairmentConfigBase):
    distribution: DistributionManager = field(default_factory=DistributionManager)

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield from self.distribution.apply(impairment)
