from typing import Generator, List, TYPE_CHECKING
from chimera_core.core.manager.base import ReserveMixin

if TYPE_CHECKING:
    from xoa_driver.v2.ports import PortChimera

from loguru import logger

from chimera_core.core.manager.flow import FlowHandler, FlowHandlerManager


class PortManager(ReserveMixin):
    def __init__(self, port: "PortChimera", reserve: bool = False) -> None:
        self.resource_instance = port
        self._reserve = reserve
        self.flows = FlowHandlerManager([FlowHandler(f) for f in port.emulation.flow])

    async def setup(self) -> "PortManager":
        if self._reserve:
            await self.reserve_if_not()
        # await self.port_instance.emulate.set_on()
        return self

    def __await__(self) -> Generator[None, None, "PortManager"]:
        return self.setup().__await__()
