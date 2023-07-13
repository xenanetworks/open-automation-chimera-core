from dataclasses import dataclass
from typing import Any, List, TYPE_CHECKING

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

from .__dataset import FlowConfig


class FlowManager:
    def __init__(self, flow: "CFlow") -> None:
        self.__flow = flow
        self.shadow_filter = ShadowFilterManager(flow.shadow_filter)
        self.drop = ImpairmentDrop(flow.drop)
        self.misordering = ImpairmentMisordering(flow.misordering)
        self.latency_jitter = ImpairmentLatencyJitter(flow.latency_jitter)
        self.duplication = ImpairmentDuplication(flow.duplication)
        self.corruption = ImpairmentCorruption(flow.corruption)
        self.policer = ImpairmentPolicer(flow.policer)
        self.shaper = ImpairmentShaper(flow.shaper)

    async def get(self) -> FlowConfig:
        """Get the flow configuration

        :return: flow configuration
        :rtype: FlowConfig
        """
        comment = (await self.__flow.comment.get()).comment
        return FlowConfig(
            comment=comment
        )

    async def set(self, config: FlowConfig) -> None:
        """Set the flow configuration

        :param config: flow configuration
        :type config: FlowConfig
        """
        await self.__flow.comment.set(comment=config.comment)

    @property
    def statistics(self) -> Any:
        """Return the flow statistics

        :return: flow statistics
        :rtype: Any
        """
        return self.__flow.statistics


@dataclass
class FlowManagerContainer:
    flows: List[FlowManager]

    def __getitem__(self, index: int) -> FlowManager:
        flow = self.flows[index]
        return flow
