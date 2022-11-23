from dataclasses import dataclass
from typing import List
from chimera_core.core.utils.helper import reserve_modules_ports

from xoa_driver.v2 import ports

from chimera_core.core.session.flow import FlowHandler, FlowHandlerManager


class PortHandler:
    def __init__(self, port: ports.PortChimera):
        self.port = port
        self.flows = FlowHandlerManager([FlowHandler(f) for f in port.emulation.flow])


@dataclass
class PortHandlerManager:
    ports: List[PortHandler]

    def __getitem__(self, index: int) -> PortHandler:
        port = self.ports[index]
        return port
