from dataclasses import dataclass
from typing import List, TYPE_CHECKING

from chimera_core.core.manager.impairment import (
    LatencyJitterConfigurator,
    ShadowFilterManager,
    ImpairmentDrop,
    ImpairmentPolicer,
)

if TYPE_CHECKING:
    from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import CFlow


class FlowManager:
    def __init__(self, flow: "CFlow"):
        self.flow = flow
        self.shadow_filter = ShadowFilterManager(flow.shadow_filter)
        self.latency_jitter = LatencyJitterConfigurator(flow.latency_jitter)
        self.drop = ImpairmentDrop(flow.drop)
        self.policer = ImpairmentPolicer(flow.policer)


@dataclass
class FlowManagerContainer:
    flows: List[FlowManager]

    def __getitem__(self, index: int) -> FlowManager:
        flow = self.flows[index]
        return flow
