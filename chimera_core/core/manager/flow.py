from dataclasses import dataclass
from typing import List, TYPE_CHECKING

from chimera_core.core.manager.impairment import (
    ImpairmentCorruption,
    ImpairmentDuplication,
    ImpairmentMisordering,
    ImpairmentLatencyJitter,
    ImpairmentShaper,
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
        self.drop = ImpairmentDrop(flow.drop)
        self.misordering = ImpairmentMisordering(flow.misordering)
        self.latency_jitter = ImpairmentLatencyJitter(flow.latency_jitter)
        self.duplication = ImpairmentDuplication(flow.duplication)
        self.corruption = ImpairmentCorruption(flow.corruption)
        self.policer = ImpairmentPolicer(flow.policer)
        self.shaper = ImpairmentShaper(flow.shaper)


@dataclass
class FlowManagerContainer:
    flows: List[FlowManager]

    def __getitem__(self, index: int) -> FlowManager:
        flow = self.flows[index]
        return flow
