from typing import Generator, List, TYPE_CHECKING
from chimera_core.core.manager.dataset import PortConfig

if TYPE_CHECKING:
    from xoa_driver.v2.ports import PortChimera

from loguru import logger
from xoa_driver.utils import apply as driver_apply
from xoa_driver import enums

from chimera_core.core.manager.base import ReserveMixin
from chimera_core.core.manager.flow import FlowManager, FlowManagerContainer


class PortConfigurator:
    def __init__(self, port: "PortChimera") -> None:
        self.port = port

    async def get(self) -> PortConfig:
        comment, tx_enable, emulate, tpld_mode, fcs_error_mode = await driver_apply(*(
            self.port.comment.get(),
            self.port.tx_enable.get(),
            self.port.emulate.get(),
            self.port.emulation.tpld_mode.get(),
            self.port.emulation.drop_fcs_errors.get(),
        ))
        logger.debug(tpld_mode.mode)
        config = PortConfig(
            comment=comment.comment,
            tx_enable=tx_enable.on_off,
            emulate=emulate.action,
            tpld_mode=tpld_mode.mode,
            fcs_error_mode=fcs_error_mode.on_off,
        )
        return config

    async def set(self, config: PortConfig) -> None:
        pass


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

