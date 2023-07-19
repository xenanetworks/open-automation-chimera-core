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
    port_speed: List[int] = field(default_factory=list)
    bypass_mode: enums.OnOff = enums.OnOff.OFF


@dataclass
class PortConfigPcsPmaBase:
    enable: enums.OnOff = enums.OnOff.OFF
    """Enable/disable"""

    duration: int = 100
    """0 ms - 1000 ms; increments of 1 ms; 0 = permanently link down."""

    period: int = 10000
    """10 ms - 50000 ms; number of ms - must be multiple of 10 ms."""

    repetition: int = 0
    """1 - 64K; 0 = continuous."""


@dataclass
class PortConfigLinkFlap(PortConfigPcsPmaBase):
    enable: enums.OnOff = enums.OnOff.OFF
    """Enable/disable link flap"""

    duration: int = 100
    """0 ms - 1000 ms; increments of 1 ms; 0 = permanently link down."""

    period: int = 1000
    """10 ms - 50000 ms; number of ms - must be multiple of 10 ms."""

    repetition: int = 0
    """1 - 64K; 0 = continuous."""


@dataclass
class PortConfigPulseError(PortConfigPcsPmaBase):
    enable: enums.OnOff = enums.OnOff.OFF
    """Enable/disable PMA errors"""

    duration: int = 100
    """0 ms - 5000m s; increments of 1 ms; 0 = constant BER."""

    period: int = 1000
    """10 ms - 50000 ms; number of ms - must be multiple of 10 ms."""

    repetition: int = 0
    """1 - 64K; 0 = continuous."""

    coeff: int = 100
    """Multiples of 0.01, 1 <= coeff <= 999, default to 100"""

    exp: int = -4
    """-3 <= exp <= -17, default to -4"""


@dataclass
class PortConfig:
    """Chimera port configuration
    """
    comment: str = ''
    """Port description"""

    enable_tx: bool = True
    """Enable/disable TX output of the port"""

    autoneg_selection: bool = False
    """Enable/disable auto-negotiation of the port"""

    enable_impairment: enums.OnOff = enums.OnOff.OFF
    """Enable/disable impairment on the port"""

    tpld_mode: enums.TPLDMode = enums.TPLDMode.NORMAL
    """Test Payload (TPLD) size.
    
    The Xena Valkyrie traffic generators support inserting a Test Payload (TPLD) into the transmitted packets. The TPLD contains meta data, which can be used by the Xena receiving device to provide miscellaneous statistics.
    
    When Chimera is connected to a Valkyrie traffic generator, Chimera can use the TPLD in the incoming packets for flow filtering.

    The TPLD supports 2 sizes:

    * Default (20 bytes)
    * Micro (6 bytes)

    To use the TPLD for filtering in Chimera, it must be configured for the same TPLD format, as the transmitting Valkyrie traffic generator.
    """

    fcs_error_mode: enums.OnOff = enums.OnOff.OFF
    """When packets with an FCS error is received on a Chimera port, they are counted by the port statistics.
    
    Chimera supports two FCS error modes:
    
    * Pass mode (OFF): In this mode FCS errored packets are processed by Chimera as any other packet. I.e. the flow filter is applied and the packet is subject to flow impairment and forwarded onto the output port.
    * Discard mode (ON): In this mode FCS errored packets are filtered by the flow filters and mapped to the corresponding impairment flow, where they are discarded and counted as OTHER DROPS.
    """

    link_flap: PortConfigLinkFlap = field(default_factory=PortConfigLinkFlap)
    """Logical Link Flap configuration.
    
    Chimera can be configured to emulate that the physical link is down or unstable. Logical link flap is implemented by scrambling the Tx PCS encoding to prevent the peer port from getting a link. I.e. it is not implemented by turning the physical transmitter on or off.
    
    Logical link flap works for both electrical cables (DAC cables) and optical cables.

    Logical link flap supports a repetitious pattern, where the link is taken down for a period (Duration) and then brought up again. This is repeated after a configurable amount of time (Repeat Period). The flapping is repeated a configurable number of times or continuously (Repetitions).
    """

    pma_error_pulse: PortConfigPulseError = field(default_factory=PortConfigPulseError)
    """PMA Error Pulse Injection configuration
    
    PMA error pulse allows the user to insert pulses of bit errors onto the link. If FEC is enabled, PMA errors are injected after the addition of the FEC bits, so that at the receiving end, FEC will correct as many of the PMA errors as possible.
    
    Notice that PMA error pulse is configured at a port level and will affect all flows configured for that port.

    Logical link flap and PMA error pulse inject are mutually exclusive.
    
    PMA errors can be inserted with a fixed distance dependent on the selected port speed. The supported distances between two adjacent PMA errors and the corresponding BER for all speeds are listed below, where n is an integer number.

    ==========  ============================  ============================
    Speed       Supported PMA error distance  Supported PMA bit error rate
    ==========  ============================  ============================
    25G / 10G   n * 256 bits                  0.39 % / n
    50G         n * 512 bits                  0.20 % / n
    40G / 100G  n * 1024 bits                 0.10 % / n
    ==========  ============================  ============================
    
    """

    def set_impairment(self, on_off: enums.OnOff) -> None:
        """Enable/disable impairment

        :param on_off: Enable/disable impairment
        :type on_off: enums.OnOff
        """
        self.enable_impairment = on_off

    def set_autoneg(self, on_off: bool) -> None:
        """Enable/disable auto-negotiation

        :param on_off: Enable/disable auto-negotiation
        :type on_off: bool
        """
        self.autoneg_selection = on_off

    def set_tpld_mode(self, mode: enums.TPLDMode) -> None:
        """Set TPLD size mode

        :param mode: TPLD size mode
        :type mode: enums.TPLDMode
        """
        self.tpld_mode = mode

    def set_fcs_error_mode(self, mode: enums.OnOff) -> None:
        """Set FCS Error mode

        :param mode: FCS Error mode
        :type mode: enums.OnOff
        """
        self.fcs_error_mode = mode

    def set_link_flap(self, 
                    enable: enums.OnOff = enums.OnOff.OFF,
                    duration: int = 100,
                    period: int = 1000,
                    repetition: int = 0) -> None:
        """Set link flap configuration

        :param enable: Enable/disable link flap
        :type enable: enums.OnOff
        :param duration: 0 ms - 1000 ms; increments of 1 ms; 0 = permanently link down.
        :type duration: int
        :param period: 10 ms - 50000 ms; number of ms - must be multiple of 10 ms.
        :type period: int
        :param repetition: 1 - 64K; 0 = continuous.
        :type repetition: int
        """
        self.link_flap.enable = enable
        self.link_flap.duration = duration
        self.link_flap.period = period
        self.link_flap.repetition = repetition

    def set_pma_error_pulse(self,
                            enable: enums.OnOff = enums.OnOff.OFF,
                            duration: int = 100, 
                            period: int = 1000, 
                            repetition: int = 0,
                            coeff: int = 100,
                            exp: int = -4) -> None:
        """PMA Error Pulse Injection configuration

        :param enable: Enable/disable PMA errors
        :type enable: enums.OnOff
        :param duration: 0 ms - 5000m s; increments of 1 ms; 0 = constant BER.
        :type duration: int
        :param period: 10 ms - 50000 ms; number of ms - must be multiple of 10 ms.
        :type period: int
        :param repetition: 1 - 64K; 0 = continuous.
        :type repetition: int
        :param coeff: Multiples of 0.01, 1 <= coeff <= 999, default to 100
        :type coeff: int
        :param exp: -3 <= exp <= -17, default to -4
        :type exp: int
        """
        self.pma_error_pulse.enable = enable
        self.pma_error_pulse.duration = duration
        self.pma_error_pulse.period = period
        self.pma_error_pulse.repetition = repetition
        self.pma_error_pulse.coeff = coeff
        self.pma_error_pulse.exp = exp

    set_impairment_on = partialmethod(set_impairment, enums.OnOff.ON)
    """Set impairment on"""
    set_impairment_off = partialmethod(set_impairment, enums.OnOff.OFF)
    """Set impairment off"""

    set_autoneg_on = partialmethod(set_autoneg, True)
    """Set auto-negotiation on"""
    set_autoneg_off = partialmethod(set_autoneg, False)
    """Set auto-negotiation off"""

    set_tpld_normal = partialmethod(set_tpld_mode, enums.TPLDMode.NORMAL)
    """Set TPLD size to normal mode"""
    set_tpld_micro = partialmethod(set_tpld_mode, enums.TPLDMode.MICRO)
    """Set TPLD size to micro mode"""

    set_fcs_error_mode_pass = partialmethod(set_fcs_error_mode, enums.OnOff.OFF)
    """Set FCS Error mode to Pass"""
    set_fcs_error_mode_discard = partialmethod(set_autoneg, enums.OnOff.ON)
    """Set FCS Error mode to Discard"""

    set_link_flap_off = partialmethod(set_link_flap, enums.OnOff.OFF)
    """Set Link Flap off"""

    set_pma_error_pulse_off = partialmethod(set_pma_error_pulse, enums.OnOff.OFF)
    """Set PMA Error Pulse off"""
    


@dataclass
class CustomDistribution:
    custom_distribution_index: int
    distribution_type: enums.LatencyTypeCustomDist
    linear: enums.OnOff
    symmetric: enums.OnOff
    entry_count: int
    data_x: List[int] = field(default_factory=list)
    comment: str = ''