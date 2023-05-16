from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, NamedTuple, Optional, Tuple, Type, TypeVar, Union, Protocol
from loguru import logger

from xoa_driver import enums
from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import (
    CLatencyJitterImpairment,
    CDropImpairment,
    CMisorderingImpairment,
    CShaperImpairment,
    CDuplicationImpairment,
    CPolicerImpairment,
    CCorruptionImpairment,
)

from chimera_core.core.manager.flow.distributions.__dataset import (
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
    DistributionConfigBase,
    TImpairmentWithDistribution,
)
from chimera_core.core.manager.__dataset import IterDataclassMixin, GeneratorToken
from chimera_core.core.manager.exception import InvalidDistributionError
from .exception import DistributionNotSetError


TImpairment = Union[
    CLatencyJitterImpairment,
    CDropImpairment,
    CMisorderingImpairment,
    CDuplicationImpairment,
    CCorruptionImpairment,
    CMisorderingImpairment,
    CShaperImpairment,
    CPolicerImpairment,
]

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

TypeTokenResponseOrError = Union[Exception, Any]


class PImpairmentConfig(Protocol):
    def apply(self, impairment: TImpairment) -> GeneratorToken:
        ...


@dataclass
class BatchReadDistributionConfigFromServer(IterDataclassMixin):
    schedule: bool = False
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
    enable: TypeTokenResponseOrError = None
    schedule: TypeTokenResponseOrError = None

    @property
    def was_set_distributions(self) -> Generator[Tuple[str, Any], None, None]:
        """if token respsonse is not NOTVALID means it was set"""
        for command_name in self._fields:
            if (command_response := getattr(self, command_name)) and not isinstance(command_response, Exception):
                yield command_name, command_response


@dataclass
class Schedule:
    duration: int = 0
    period: int = 0

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
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

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield from self.schedule.apply(impairment)


distribution_class: Dict[str, Type[DistributionConfigBase]] = {
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

@dataclass
class ImpairmentConfigBase(ABC):
    @abstractmethod
    def start(self, impairment: TImpairmentGeneral) -> GeneratorToken:
        raise NotImplementedError

    @abstractmethod
    def stop(self, impairment: TImpairmentGeneral) -> GeneratorToken:
        raise NotImplementedError

    @abstractmethod
    def apply(self, impairment: TImpairmentGeneral) -> GeneratorToken:
        raise NotImplementedError


@dataclass
class ImpairmentConfigGeneral(ImpairmentConfigBase):
    read_distribution_config_from_server: BatchReadDistributionConfigFromServer
    allow_set_distribution_class_name: Tuple[str, ...]
    _current_distribution: Optional[DistributionConfigBase] = None
    enable: enums.OnOff = enums.OnOff.OFF

    def apply(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield from self.apply_distribution(impairment)

    def apply_distribution(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        if self._current_distribution:
            yield from self._current_distribution.apply(impairment)
        else:
            raise DistributionNotSetError()

    def stop(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.enable.set(enums.OnOff.OFF)

    def start(self, impairment: TImpairmentWithDistribution) -> GeneratorToken:
        yield impairment.enable.set(self.enable)
        yield from self.apply_distribution(impairment)

    def get_current_distribution(self) -> Optional[DistributionConfigBase]:
        return self._current_distribution

    def set_schedule(self, schedule_respsonse: Any) -> None:
        if (distribution := self.get_current_distribution()) \
            and isinstance(distribution, DistributionWithNonBurstSchedule):
            distribution.schedule.duration = schedule_respsonse.duration
            distribution.schedule.period = schedule_respsonse.period

    def load_value_from_server_response(self, validator: DistributionResponseValidator) -> None:
        for distribution_name, distribution_response in validator.was_set_distributions:
            if distribution_name == 'enable':
                self.enable = enums.OnOff(distribution_response.action)
            elif distribution_name == 'schedule':
                self.set_schedule(distribution_response)
            else:
                distribution_config = distribution_class[distribution_name]()
                distribution_config.load_token_response_value(distribution_response)
                self.set_distribution(distribution_config)

    def set_distribution(self, distribution: DistributionConfigBase) -> None:
        logger.debug(self)
        logger.debug(distribution.__class__.__name__)
        logger.debug(self.allow_set_distribution_class_name)
        if distribution.__class__.__name__ not in self.allow_set_distribution_class_name:
            raise InvalidDistributionError(self.allow_set_distribution_class_name)
        self._current_distribution = distribution


@dataclass
class ImpairmentConfigPolicer:
    on_off: enums.OnOff = enums.OnOff.OFF
    mode: enums.PolicerMode = enums.PolicerMode.L2
    cir: int = 0
    cbs: int = 0

    async def apply(self, impairment: CPolicerImpairment) -> None:
        impairment.config.set(
            on_off=self.on_off,
            mode=self.mode,
            cir=self.cir,
            cbs=self.cbs,
        )


    def start(self, impairment: CPolicerImpairment) -> GeneratorToken:
        yield impairment.config.set(
            on_off=enums.OnOff.ON,
            mode=self.mode,
            cir=self.cir,
            cbs=self.cbs,
        )


@dataclass
class ImpairmentConfigShaper:
    on_off: enums.OnOff = enums.OnOff.OFF
    mode: enums.PolicerMode = enums.PolicerMode.L2
    cir: int = 0
    cbs: int = 0
    buffer_size: int = 0

    def apply(self, impairment: CShaperImpairment) -> GeneratorToken:
        yield impairment.config.set(
            on_off=self.on_off,
            mode=self.mode,
            cir=self.cir,
            cbs=self.cbs,
            buffer_size=self.buffer_size,
        )


    def start(self, impairment: CShaperImpairment) -> GeneratorToken:
        yield impairment.config.set(
            on_off=enums.OnOff.ON,
            mode=self.mode,
            cir=self.cir,
            cbs=self.cbs,
            buffer_size=self.buffer_size,
        )


@dataclass
class ImpairmentConfigCorruption(ImpairmentConfigGeneral):
    corruption_type: enums.CorruptionType = enums.CorruptionType.ETH

    def apply(self, impairment: CCorruptionImpairment) -> GeneratorToken:
        yield impairment.type.set(self.corruption_type)
        yield from super().apply(impairment)