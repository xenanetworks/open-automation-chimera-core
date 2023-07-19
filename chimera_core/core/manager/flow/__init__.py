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
    from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import CFlow, CPerFlowStats

from .__dataset import FlowConfig


class FlowManager:
    def __init__(self, flow: "CFlow") -> None:
        self.__flow = flow
        self.shadow_filter = ShadowFilterManager(flow.shadow_filter)
        """
        Flow filters can be updated during runtime with traffic applied to the input ports.

        To guarantee that filtering is always coherent, Chimera implements two sets of registers in the flow filters:

        * Working registers: used for flow filtering.
        * Shadow registers: used for updating flow filters.

        All registers in the flow filters have both a working register and a shadow register.

        Shadow registers can be written and read, while working registers can only be read.
        """

        self.drop = ImpairmentDrop(flow.drop)
        """
        Packet drop will cause packets to be removed from the Ethernet packet flow.
        """

        self.misordering = ImpairmentMisordering(flow.misordering)
        """
        Misordering causes packets to be taken out of the Ethernet packet flow and delayed for a configurable number of packets, after which they are re-inserted into the packet flow. The number of packets that the packet is delayed is referred to as the Misorder Depth.

        At any point in time, only a single packet can be in queue to be re-inserted. As a result, the following limitation applies to the values of probability and depth.
        """

        self.latency_jitter = ImpairmentLatencyJitter(flow.latency_jitter)
        """
        The latency / jitter impairment differs significantly from the other impairments described above, because it affects the delay of each packet. As a consequence, the distributions which can be assigned to the latency / jitter impairment define latencies rather than the distance in packets between two impaired packets.
        """

        self.duplication = ImpairmentDuplication(flow.duplication)
        """
        Packet duplication will duplicate a packet, so the packet is transmitted twice in the Ethernet packet flow. The duplicate packet is inserted right after the original packet.

        Notice that packet duplication is located after the shapers, just before the Tx port in the impairment pipeline. This means enabling packet duplication will add packets to the packet flow after the shapers, hereby increasing the BW compared to what was configured in the shaper.
        """

        self.corruption = ImpairmentCorruption(flow.corruption)
        """
        Chimera supports packet corruption at the following protocol layers:

        * Ethernet FCS
        * IP
        * TCP
        * UDP

        Corruption is done by altering a bit in the checksum for the configured protocol. Furthermore, when corruption is done at IP / TCP / UDP level, the Ethernet FCS is corrected, so the checksum error only appears at the configured level.

        Note: when configuring corruption at IP / TCP / UDP level, the flow filter must include the selected layer in the flow filter.

        I.e., if corruption is configured at the UDP level, the flow filter must include all relevant protocols:

        * Ethernet
        * (optionally) VLAN(s) / MPLS
        * IPv4 / IPv6
        * UDP

        This implies that IP / TCP / UDP corruption is not supported for the port default flow (flow = 0), because this flow has no filter.
        """

        self.policer = ImpairmentPolicer(flow.policer)
        """
        Ingress bandwidth policer
        """

        self.shaper = ImpairmentShaper(flow.shaper)
        """
        Notice that the shapers are located before the packet duplication in the impairment pipeline. I.e., if packet duplication is configured, duplicate packets are added to the flow after the shaper, and the resulting output bandwidth will be higher than the one configured in the shaper.

        Furthermore, the amount of memory allocated for the shaper buffer will be taken from the buffer used for generating latency, so when memory is allocated for shaper buffering, the guaranteed lossless latency will decrease accordingly.
        """

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
    def statistics(self) -> "CPerFlowStats":
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
