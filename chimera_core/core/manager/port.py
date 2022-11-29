from typing import Generator, List, TYPE_CHECKING

if TYPE_CHECKING:
    from xoa_driver.v2.ports import PortChimera

from loguru import logger

from chimera_core.core.manager.base import ReserveMixin
from chimera_core.core.manager.flow import FlowManager, FlowManagerContainer


class PortManager(ReserveMixin):
    def __init__(self, port: "PortChimera") -> None:
        self.resource_instance = port
        self.flows = FlowManagerContainer([FlowManager(f) for f in port.emulation.flow])

    async def setup(self) -> "PortManager":
        # await self.port_instance.emulate.set_on()
        return self

    def __await__(self) -> Generator[None, None, "PortManager"]:
        return self.setup().__await__()
