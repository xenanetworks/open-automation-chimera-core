from dataclasses import dataclass
from typing import List, TYPE_CHECKING

from chimera_core.core.session.Impairment import LatencyJitterHandler

if TYPE_CHECKING:
    from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import CFlow


class FlowHandler:
    def __init__(self, flow: "CFlow"):
        self.flow = flow
        self.latency_jitter = LatencyJitterHandler(flow.latency_jitter)


@dataclass
class FlowHandlerManager:
    flows: List[FlowHandler]

    def __getitem__(self, index: int) -> FlowHandler:
        flow = self.flows[index]
        return flow
