import asyncio
from typing import Generator, List, TYPE_CHECKING

if TYPE_CHECKING:
    from xoa_driver.v2.ports import PortChimera

from xoa_driver import enums
from xoa_driver import utils

from chimera_core.core.manager.__dataset import PortConfig, PortConfigLinkFlap, PortConfigPulseError
from chimera_core.core.manager.__base import ReserveMixin
from chimera_core.core.manager.flow import FlowManager, FlowManagerContainer


class PortConfigurator:
    def __init__(self, port: "PortChimera") -> None:
        self.port = port

    async def get(self) -> PortConfig:
        comment, enable_tx, enable_link_flap, link_flap_params, enable_pulse_error, pulse_error_params, \
            emulate, tpld_mode, fcs_error_mode = await asyncio.gather(*(
                self.port.comment.get(),
                self.port.tx_enable.get(),
                self.port.pcs_pma.link_flap.enable.get(),
                self.port.pcs_pma.link_flap.params.get(),
                self.port.pcs_pma.pma_pulse_err_inj.enable.get(),
                self.port.pcs_pma.pma_pulse_err_inj.params.get(),
                self.port.emulate.get(),
                self.port.emulation.tpld_mode.get(),
                self.port.emulation.drop_fcs_errors.get(),
            ))
        link_flap = PortConfigLinkFlap(
            enable=enums.OnOff(enable_link_flap.on_off),
            duration=link_flap_params.duration,
            period=link_flap_params.period,
            repetition=link_flap_params.repetition,
        )
        pulse_error = PortConfigPulseError(
            enable=enums.OnOff(enable_pulse_error.on_off),
            duration=pulse_error_params.duration,
            period=pulse_error_params.period,
            repetition=pulse_error_params.repetition,
            coeff=pulse_error_params.coeff,
            exp=pulse_error_params.exp,
        )
        config = PortConfig(
            comment=comment.comment,
            link_flap=link_flap,
            pulse_error=pulse_error,
            enable_tx=enable_tx.on_off,
            emulate=emulate.action,
            tpld_mode=tpld_mode.mode,
            fcs_error_mode=fcs_error_mode.on_off,
        )
        return config

    async def set(self, config: PortConfig) -> None:
        await utils.apply(*(
            self.port.comment.set(config.comment),
            self.port.pcs_pma.link_flap.enable.set(config.link_flap.enable),
            self.port.pcs_pma.link_flap.params.set(
                duration=config.link_flap.duration,
                period=config.link_flap.period,
                repetition=config.link_flap.repetition
            ),
            self.port.pcs_pma.pma_pulse_err_inj.enable.set(config.pulse_error.enable),
            self.port.pcs_pma.pma_pulse_err_inj.params.set(
                duration=config.pulse_error.duration,
                period=config.pulse_error.period,
                repetition=config.pulse_error.repetition,
                coeff=config.pulse_error.coeff,
                exp=config.pulse_error.exp,
            ),
            self.port.emulate.set(config.emulate),
            self.port.emulation.tpld_mode.set(config.tpld_mode),
            self.port.emulation.drop_fcs_errors.set(config.fcs_error_mode),
        ))


class PortManager(ReserveMixin):
    def __init__(self, port: "PortChimera") -> None:
        self.resource_instance = port
        self.config = PortConfigurator(port)
        self.flows = FlowManagerContainer([FlowManager(f) for f in port.emulation.flow])

    async def setup(self) -> "PortManager":
        # await self.port_instance.emulate.set_on()
        return self

    def __await__(self) -> Generator[None, None, "PortManager"]:
        return self.setup().__await__()
