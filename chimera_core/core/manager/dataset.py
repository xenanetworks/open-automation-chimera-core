import ipaddress
from dataclasses import dataclass, field, fields
from typing import Any, Callable, Coroutine, Dict, Generator, Generic, List, NamedTuple, Optional, Protocol, Tuple, Type, TypeVar, Union, cast
from enum import Enum
from functools import partial, partialmethod
from loguru import logger

from pydantic import BaseModel
from xoa_driver import enums
from xoa_driver.v2 import misc
from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import (
    CLatencyJitterImpairment,
    CDropImpairment,
    CMisorderingImpairment,
    CShaperImpairment,
)


INTERVEL_CHECK_RESERVE_RESOURCE = 0.01
TPLD_FILTERS_LENGTH = 16

GeneratorToken = Generator[misc.Token, None, None]

class PortConfigPcsPmaBase(BaseModel):
    enable: enums.OnOff = enums.OnOff.OFF
    duration: int = 100
    period: int = 10000
    repetition: int = 0


class PortConfigLinkFlap(PortConfigPcsPmaBase):
    pass


class PortConfigPulseError(PortConfigPcsPmaBase):
    coeff: int = 1
    exp: int = -4


@dataclass
class PortConfig:
    comment: str = ''
    enable_tx: bool = True
    autoneg_selection: bool = False
    emulate: enums.OnOff = enums.OnOff.OFF
    tpld_mode: enums.TPLDMode = enums.TPLDMode.NORMAL
    fcs_error_mode: enums.OnOff = enums.OnOff.OFF
    link_flap: PortConfigLinkFlap = field(default_factory=PortConfigLinkFlap)
    pulse_error: PortConfigPulseError = field(default_factory=PortConfigPulseError)

    def set_emulate(self, on_off: enums.OnOff) -> None:
        self.emulate = on_off

    set_emulate_on = partialmethod(set_emulate, enums.OnOff.ON)
    set_emulate_off = partialmethod(set_emulate, enums.OnOff.OFF)


class ModuleConfig(BaseModel):
    comment: str = ''
    timing_source: enums.TimingSource = enums.TimingSource.CHASSIS
    clock_ppb: int = 1
    tx_clock_source: enums.TXClockSource = enums.TXClockSource.MODULELOCALCLOCK
    tx_clock_status: enums.TXClockStatus = enums.TXClockStatus.OK
    latency_mode: enums.ImpairmentLatencyMode = enums.ImpairmentLatencyMode.NORMAL
    cfp_type: enums.MediaCFPType = enums.MediaCFPType.CFP_UNKNOWN
    cfp_state: enums.MediaCFPState = enums.MediaCFPState.NOT_CFP
    port_count: int = 0
    port_speed: int = 0
    bypass_mode: enums.OnOff = enums.OnOff.OFF


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
    posion: TypeExceptionAny = None
    custom: TypeExceptionAny = None
    accumulate_and_burst: TypeExceptionAny = None
    constant_delay: TypeExceptionAny = None
    step: TypeExceptionAny = None

    @property
    def filter_valid_distribution(self) -> Generator[Tuple[str, Any], None, None]:
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
class ImpairmentConfigBase:
    enable: enums.OnOff = enums.OnOff.OFF


@dataclass
class ImpairmentConfigCorruption:
    corruption_type: enums.CorruptionType = enums.CorruptionType.ETH
    distribution: DistributionManager = field(default_factory=DistributionManager)

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield from self.distribution.apply(impairment)


@dataclass
class ImpairmentWithDistribution(ImpairmentConfigBase):
    distribution: DistributionManager = field(default_factory=DistributionManager)

    def apply(self, impairment: TImpairment) -> GeneratorToken:
        yield from self.distribution.apply(impairment)


@dataclass
class ImpairmentConfigPolicer:
    on_off: enums.OnOff = enums.OnOff.OFF
    mode: enums.PolicerMode = enums.PolicerMode.L2
    cir: int = 0
    cbs: int = 0


@dataclass
class ImpairmentConfigShaper:
    on_off: enums.OnOff = enums.OnOff.OFF
    mode: enums.PolicerMode = enums.PolicerMode.L2
    cir: int = 0
    cbs: int = 0
    buffer_size: int = 0

    async def set(self, impairment: CShaperImpairment) -> None:
        impairment.config.set(
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

class LatencyJitterConfigMain(ImpairmentConfigBase):
    constant_delay: ConstantDelay = ConstantDelay()


FFF_HEX = 'FFF'


class InnerOuter(BaseModel):
    use: enums.OnOff = enums.OnOff.OFF
    mask: str = FFF_HEX
    value: int = 0

    def off(self) -> None:
        self.use = enums.OnOff.OFF

    def on(self, value: int = 0, mask: str = FFF_HEX) -> None:
        self.use = enums.OnOff.ON
        self.value = value
        self.mask = mask


class FilterConfigCommon(BaseModel):
    filter_use: enums.FilterUse = enums.FilterUse.OFF
    match_action: enums.InfoAction = enums.InfoAction.INCLUDE

    @property
    def is_off(self) -> bool:
        return self.filter_use == enums.FilterUse.OFF

    def include(self) -> None:
        self.filter_use = enums.FilterUse.AND
        self.match_action = enums.InfoAction.INCLUDE

    def exclude(self) -> None:
        self.filter_use = enums.FilterUse.AND
        self.match_action = enums.InfoAction.EXCLUDE

    def _use_and(self) -> None:
        self.filter_use = enums.FilterUse.AND

    def _use_off(self) -> None:
        self.filter_use = enums.FilterUse.OFF

    def action(self, include=True):
        self.match_action = enums.InfoAction.INCLUDE if include else enums.InfoAction.EXCLUDE


class ShadowFilterConfigEthernetAddr(InnerOuter):
    value: str = '000000000000'

    def on(self, value: str = '000000000000', mask: str = 'FFFFFFFFFFFF') -> None:
        self.use = enums.OnOff.ON
        self.value = value
        self.mask = mask


class ShadowFilterConfigEthernet(FilterConfigCommon):
    src_addr: ShadowFilterConfigEthernetAddr = ShadowFilterConfigEthernetAddr()
    dest_addr: ShadowFilterConfigEthernetAddr = ShadowFilterConfigEthernetAddr()


class ShadowFilterConfigL2VLAN(FilterConfigCommon):
    # inner
    tag_inner: InnerOuter = InnerOuter()
    pcp_inner: InnerOuter = InnerOuter()
    # outer
    tag_outer: InnerOuter = InnerOuter()
    pcp_outer: InnerOuter = InnerOuter()


class ShadowFilterConfigL2MPLS(FilterConfigCommon):
    label: InnerOuter = InnerOuter()
    toc: InnerOuter = InnerOuter()


class ShadowFilterLayer2Plus(BaseModel):
    present: enums.L2PlusPresent = enums.L2PlusPresent.NA
    vlan: ShadowFilterConfigL2VLAN = ShadowFilterConfigL2VLAN()
    mpls: ShadowFilterConfigL2MPLS = ShadowFilterConfigL2MPLS()

    def use_none(self) -> None:
        self.present = enums.L2PlusPresent.NA

    def use_1_vlan_tag(self) -> ShadowFilterConfigL2VLAN:
        self.present = enums.L2PlusPresent.VLAN1
        return self.vlan

    def use_2_vlan_tags(self) -> ShadowFilterConfigL2VLAN:
        self.present = enums.L2PlusPresent.VLAN2
        return self.vlan

    def use_mpls(self) -> ShadowFilterConfigL2MPLS:
        self.present = enums.L2PlusPresent.MPLS
        return self.mpls


TypeIPv4 = Union[str, int, ipaddress.IPv4Address]


class ShadowFilterConfigL2IPv4Addr(InnerOuter):
    value: TypeIPv4 = '0.0.0.0'

    def on(self, address: TypeIPv4 = '0.0.0.0', mask: str = 'FFFFFFFF') -> None:
        self.use = enums.OnOff.ON
        self.value = address
        self.mask = mask


class ShadowFilterConfigL2IPv4DSCP(InnerOuter):
    pass


class ShadowFilterConfigL3IPv4(FilterConfigCommon):
    src_addr: ShadowFilterConfigL2IPv4Addr = ShadowFilterConfigL2IPv4Addr()
    dest_addr: ShadowFilterConfigL2IPv4Addr = ShadowFilterConfigL2IPv4Addr()
    dscp: ShadowFilterConfigL2IPv4DSCP = ShadowFilterConfigL2IPv4DSCP()


class ShadowFilterConfigBasicIPv6SRCADDR(InnerOuter):
    value: str = '::'
    mask: str = 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'

    def on(self, value: str = '00000000000000000000000000000000', mask: str = 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF') -> None:
        self.use = enums.OnOff.ON
        self.value = value
        self.mask = mask


class ShadowFilterConfigBasicIPv6DESTADDR(ShadowFilterConfigBasicIPv6SRCADDR):
    pass


class ShadowFilterConfigL3IPv6(FilterConfigCommon):
    src_addr: ShadowFilterConfigBasicIPv6SRCADDR = ShadowFilterConfigBasicIPv6SRCADDR()
    dest_addr: ShadowFilterConfigBasicIPv6DESTADDR = ShadowFilterConfigBasicIPv6DESTADDR()


class ShadowFilterLayer3(BaseModel):
    present: enums.L3PlusPresent = enums.L3PlusPresent.NA
    ipv4: ShadowFilterConfigL3IPv4 = ShadowFilterConfigL3IPv4()
    ipv6: ShadowFilterConfigL3IPv6 = ShadowFilterConfigL3IPv6()

    def use_none(self) -> None:
        self.present = enums.L3PlusPresent.NA

    def use_ipv4(self) -> ShadowFilterConfigL3IPv4:
        self.present = enums.L3PlusPresent.IP4
        return self.ipv4

    def use_ipv6(self) -> ShadowFilterConfigL3IPv6:
        self.present = enums.L3PlusPresent.IP6
        return self.ipv6


class ShadowFilterConfigL4UDPSRCPort(InnerOuter):
    pass


class ShadowFilterConfigL4UDPDESTPort(InnerOuter):
    pass


class ShadowFilterConfigL4TCP(FilterConfigCommon):
    src_port: InnerOuter = InnerOuter()
    dest_port: InnerOuter = InnerOuter()


class ShadowFilterConfigL4UDP(ShadowFilterConfigL4TCP):
    pass


class ShadowFilterLayer4(BaseModel):
    tcp: ShadowFilterConfigL4TCP = ShadowFilterConfigL4TCP()
    udp: ShadowFilterConfigL4UDP = ShadowFilterConfigL4UDP()

    def use_none(self) -> None:
        pass

    def use_tcp(self) -> ShadowFilterConfigL4TCP:
        return self.tcp

    def use_udp(self) -> ShadowFilterConfigL4UDP:
        return self.udp


@dataclass
class ShadowFilterConfigTPLDID:
    filter_index: int
    tpld_id: int = 0
    use: enums.OnOff = enums.OnOff.OFF

    def on(self, tpld_id: int) -> None:
        self.use = enums.OnOff.ON
        self.tpld_id = tpld_id


class ShadowFilterConfigTPLD(FilterConfigCommon):
    configs: Tuple[ShadowFilterConfigTPLDID, ...] = tuple(ShadowFilterConfigTPLDID(filter_index=i) for i in range(16))


class ShadowFilterLayerXena(BaseModel):
    tpld: ShadowFilterConfigTPLD = ShadowFilterConfigTPLD()

    def use_tpld(self) -> ShadowFilterConfigTPLD:
        self.tpld._use_and()
        return self.tpld


class ShadowFilterConfigAnyField(FilterConfigCommon):
    position: int = 0
    value: str = '000000000000'
    mask: str = 'FFFFFFFFFFFF'

    def on(self, position: int, value: str = '000000000000', mask: str = 'FFFFFFFFFFFF') -> None:
        self.position = position
        self.value = value
        self.mask = mask


class ShadowFilterLayerAny(FilterConfigCommon):
    any_field: ShadowFilterConfigAnyField = ShadowFilterConfigAnyField()

    def use_any_field(self) -> ShadowFilterConfigAnyField:
        self.any_field._use_and()
        return self.any_field


class ShadowFilterLayer2(BaseModel):
    ethernet: ShadowFilterConfigEthernet = ShadowFilterConfigEthernet()

    def use_ethernet(self) -> ShadowFilterConfigEthernet:
        return self.ethernet


class ShadowFilterConfigBasic(BaseModel):
    layer_2: ShadowFilterLayer2 = ShadowFilterLayer2()
    layer_2_plus: ShadowFilterLayer2Plus = ShadowFilterLayer2Plus()
    layer_3: ShadowFilterLayer3 = ShadowFilterLayer3()
    layer_4: ShadowFilterLayer4 = ShadowFilterLayer4()
    layer_xena: ShadowFilterLayerXena = ShadowFilterLayerXena()
    layer_any: ShadowFilterLayerAny = ShadowFilterLayerAny()


class ProtocolSegement(BaseModel):
    protocol_type: enums.ProtocolOption
    value: str
    mask: str


class ShadowFilterConfigExtended(BaseModel):
    protocol_segments: Tuple[ProtocolSegement, ...] = tuple()
