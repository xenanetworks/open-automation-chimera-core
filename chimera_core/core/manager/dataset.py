from typing import Optional, Union

from pydantic import BaseModel
from xoa_driver import enums


INTERVEL_CHECK_RESERVE_RESOURCE = 0.01


class PortConfigLinkFlap(BaseModel):
    enable: bool = True
    duration: int = 100
    repeat_period: int = 10000
    repetition: int = 0


class PortConfig(BaseModel):
    comment: str = ''
    tx_enable: bool = True
    emulate: bool = False
    tpld_mode: enums.TPLDMode = enums.TPLDMode.NORMAL
    fcs_error_mode: enums.OnOff = enums.OnOff.OFF

    # impairment: Optional[Union[PortConfigLinkFlap]] = None


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
