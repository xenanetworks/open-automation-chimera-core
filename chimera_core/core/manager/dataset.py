from typing import Optional

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


class LatencyJitterConfigDistribution(BaseModel):
    constant_delay: Optional[int] = None


class LatencyJitterConfigSchedule(BaseModel):
    duration: Optional[int] = None
    period: Optional[int] = None


class LatencyJitterConfigMain(BaseModel):
    distribution: LatencyJitterConfigDistribution
    schedule: Optional[LatencyJitterConfigSchedule] = None
    enable: Optional[bool] = None


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
    l2plus_use: enums.L2PlusPresent = enums.L2PlusPresent.NA
    vlan: ShadowFilterConfigBasicVLAN = ShadowFilterConfigBasicVLAN()
