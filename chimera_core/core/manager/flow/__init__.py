from dataclasses import dataclass
from typing import List, TYPE_CHECKING

from .impairments.drop import ImpairmentDrop
from .impairments.duplication import ImpairmentDuplication
from .impairments.corruption import ImpairmentCorruption
from .impairments.latency_jitter import ImpairmentLatencyJitter
from .impairments.misordering import ImpairmentMisordering
from .impairments.policer import ImpairmentPolicer
from .impairments.shaper import ImpairmentShaper
from .shadow_filter import ShadowFilterManager


if TYPE_CHECKING:
    from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import CFlow


class FlowManager:
    def __init__(self, flow: "CFlow") -> None:
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
