from dataclasses import dataclass, field, fields
from functools import partialmethod
from typing import Generator, List

from chimera_core.types import enums
from xoa_driver.v2.misc import Token


GeneratorToken = Generator[Token, None, None]


class IterDataclassMixin:
    def __iter__(self):
        return iter(fields(self)) # type: ignore


@dataclass
class ModuleConfig:
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


@dataclass
class PortConfigPcsPmaBase:
    enable: enums.OnOff = enums.OnOff.OFF
    duration: int = 100
    period: int = 10000
    repetition: int = 0


@dataclass
class PortConfigLinkFlap(PortConfigPcsPmaBase):
    pass


@dataclass
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


@dataclass
class CustomDistribution:
    custom_distribution_index: int
    distribution_type: enums.LatencyTypeCustomDist
    linear: enums.OnOff
    symmetric: enums.OnOff
    entry_count: int
    data_x: List[int] = field(default_factory=list)
    comment: str = ''