import ipaddress
from typing import Any, NamedTuple, Optional, Union
from loguru import logger

from pydantic import BaseModel
from xoa_driver import enums


INTERVEL_CHECK_RESERVE_RESOURCE = 0.01


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


class PortConfig(BaseModel):
    comment: str = ''
    enable_tx: bool = True
    autoneg_selection: bool = False
    emulate: enums.OnOff = enums.OnOff.OFF
    tpld_mode: enums.TPLDMode = enums.TPLDMode.NORMAL
    fcs_error_mode: enums.OnOff = enums.OnOff.OFF
    link_flap: PortConfigLinkFlap = PortConfigLinkFlap()
    pulse_error: PortConfigPulseError = PortConfigPulseError()


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


class ImpairmentConfigCommonEnable(BaseModel):
    enable: enums.OnOff = enums.OnOff.OFF


class Schedule(BaseModel):
    duration: int = 1
    period: int = 0


class ImpairmentConfigCommonEnableSchedule(ImpairmentConfigCommonEnable):
    schedule: Schedule = Schedule()


class LatencyJitterConfigMain(ImpairmentConfigCommonEnableSchedule):
    constant_delay: int = 1


TypeExceptionAny = Union[Exception, Any, None]  # how do you typing "GetDataAttr" instead of any?


class DistributionResponseValidator(NamedTuple):
    """If query get command not return NOTVALID, the command was being set"""
    fixed_burst: TypeExceptionAny = None
    random: TypeExceptionAny = None
    fixed: TypeExceptionAny = None
    bit_error_rate: TypeExceptionAny = None
    ge: TypeExceptionAny = None
    uniform: TypeExceptionAny = None
    gaussian: TypeExceptionAny = None
    gamma: TypeExceptionAny = None
    poison: TypeExceptionAny = None
    custom: TypeExceptionAny = None
    accumulate_and_burst: TypeExceptionAny = None
    constant_delay: TypeExceptionAny = None
    step: TypeExceptionAny = None

    @property
    def enabled_distribution(self) -> Optional[str]:
        for command_name in self._fields:
            command_response = getattr(self, command_name)
            if command_response is None or isinstance(command_response, Exception):
                continue
            return command_name


class DistributionConfigBase(BaseModel):
    def __iter__(self):
        return iter(self.__fields__)


class FixedBurst(DistributionConfigBase):
    burst_size: int = 0


class DropConfigMain(ImpairmentConfigCommonEnableSchedule):
    current_dist: str = ''
    fixed_burst: FixedBurst = FixedBurst()

    def load_value_from_validator(self, validator: DistributionResponseValidator) -> None:
        if (enabled_distribution_name := validator.enabled_distribution):
            logger.debug(enabled_distribution_name)
            distribution_config = getattr(self, enabled_distribution_name)
            distribution_response = getattr(validator, enabled_distribution_name)
            for key in distribution_config:
                response_value = getattr(distribution_response, key, None)
                if response_value is None:
                    raise ValueError("it could not be none")
                setattr(distribution_config, key, response_value)


class ShadowFilterConfigBasicCommon(BaseModel):
    use: enums.FilterUse = enums.FilterUse.OFF
    action: enums.InfoAction = enums.InfoAction.INCLUDE


class ShadowFilterConfigBasicSub(BaseModel):
    use: enums.OnOff = enums.OnOff.OFF
    value: int = 0
    mask: str = '0xff'


class ShadowFilterConfigBasicIPv4SRCADDR(ShadowFilterConfigBasicSub):
    value: Union[str, int, ipaddress.IPv4Address] = '0.0.0.0'


class ShadowFilterConfigBasicIPv4DESTADDR(ShadowFilterConfigBasicIPv4SRCADDR):
    pass


class ShadowFilterConfigBasicIPv4DSCP(ShadowFilterConfigBasicSub):
    pass


class ShadowFilterConfigBasicIPv6SRCADDR(ShadowFilterConfigBasicSub):
    value: Union[str, ipaddress.IPv6Address] = '0x00000000000000000000000000000000'


class ShadowFilterConfigBasicIPv6DESTADDR(ShadowFilterConfigBasicIPv6SRCADDR):
    pass


class ShadowFilterConfigBasicIPv4Main(ShadowFilterConfigBasicCommon):
    src_addr: ShadowFilterConfigBasicIPv4SRCADDR = ShadowFilterConfigBasicIPv4SRCADDR()
    dest_addr: ShadowFilterConfigBasicIPv4DESTADDR = ShadowFilterConfigBasicIPv4DESTADDR()
    dscp: ShadowFilterConfigBasicIPv4DSCP = ShadowFilterConfigBasicIPv4DSCP()


class ShadowFilterConfigBasicIPv6Main(ShadowFilterConfigBasicCommon):
    src_addr: ShadowFilterConfigBasicIPv6SRCADDR = ShadowFilterConfigBasicIPv6SRCADDR()
    dest_addr: ShadowFilterConfigBasicIPv6DESTADDR = ShadowFilterConfigBasicIPv6DESTADDR()


class ShadowFilterConfigBasicEthernet(BaseModel):
    use: enums.FilterUse = enums.FilterUse.OFF
    action: enums.InfoAction = enums.InfoAction.INCLUDE
    use_src_addr: enums.OnOff = enums.OnOff.OFF
    value_src_addr: str = "0x000000000000"
    mask_src_addr: str = "0xFFFFFFFFFFFF"
    use_dest_addr: enums.OnOff = enums.OnOff.OFF
    value_dest_addr: str = "0x000000000000"
    mask_dest_addr: str = "0xFFFFFFFFFFFF"


class ShadowFilterConfigBasicVLAN(BaseModel):
    use: enums.FilterUse = enums.FilterUse.OFF
    action: enums.InfoAction = enums.InfoAction.INCLUDE
    # inner
    use_tag_inner: enums.OnOff = enums.OnOff.OFF
    value_tag_inner: int = 0
    mask_tag_inner: str = "0xFFF"
    use_pcp_inner: enums.OnOff = enums.OnOff.OFF
    value_pcp_inner: int = 0
    mask_pcp_inner: str = "0xFFF"
    # outer
    use_tag_outer: enums.OnOff = enums.OnOff.OFF
    value_tag_outer: int = 0
    mask_tag_outer: str = "0xFFF"
    use_pcp_outer: enums.OnOff = enums.OnOff.OFF
    value_pcp_outer: int = 0
    mask_pcp_outer: str = "0xFFF"


class ShadowFilterConfigBasic(BaseModel):
    ethernet: ShadowFilterConfigBasicEthernet = ShadowFilterConfigBasicEthernet()
    use_l2plus: enums.L2PlusPresent = enums.L2PlusPresent.NA
    vlan: ShadowFilterConfigBasicVLAN = ShadowFilterConfigBasicVLAN()
    use_l3: enums.L3PlusPresent = enums.L3PlusPresent.NA
    ipv4: ShadowFilterConfigBasicIPv4Main = ShadowFilterConfigBasicIPv4Main()
    ipv6: ShadowFilterConfigBasicIPv6Main = ShadowFilterConfigBasicIPv6Main()
