from dataclasses import dataclass
from typing import Generator, List
from chimera_core.core.utils.helper import reserve_modules_ports

from xoa_driver.v2 import ports
from loguru import logger

from chimera_core.core.session.flow import FlowHandler, FlowHandlerManager


class PortHandler:
    def __init__(self, port: "ports.PortChimera") -> None:
        self.port_instance = port
        self.flows = FlowHandlerManager([FlowHandler(f) for f in port.emulation.flow])

    async def setup(self) -> "PortHandler":
        logger.debug('called')
        await reserve_modules_ports(self.port_instance)
        await self.port_instance.emulate.set_on()
        return self

    def __await__(self) -> Generator[None, None, "PortHandler"]:
        return self.setup().__await__()


@dataclass
class PortHandlerManager:
    ports: List[PortHandler]

    async def __getitem__(self, index: int) -> PortHandler:
        port = self.ports[index]
        return port
