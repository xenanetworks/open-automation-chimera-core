import asyncio
from typing import TYPE_CHECKING, Optional

from loguru import logger
from xoa_driver import utils, enums
from xoa_driver.v2 import misc

from xoa_driver.internals.hli_v2.ports.port_l23.chimera.filter_definition.general import ModeBasic

from .dataset import LatencyJitterConfigDistribution, LatencyJitterConfigMain, LatencyJitterConfigSchedule, ShadowFilterConfigBasic, ShadowFilterConfigBasicEthernet

if TYPE_CHECKING:
    from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import CLatencyJitterImpairment, CDropImpairment
    from xoa_driver.internals.hli_v2.ports.port_l23.chimera.filter_definition.shadow import FilterDefinitionShadow

class LatencyJitter:
    def __init__(self, impairment: "CLatencyJitterImpairment"):
        self.impairment = impairment

    async def get(self) -> LatencyJitterConfigMain:
        enable, schedule = await utils.apply(
            self.impairment.enable.get(),
            self.impairment.schedule.get(),
        )

        return LatencyJitterConfigMain(
            enable=enable.action,
            distribution=LatencyJitterConfigDistribution(),
            schedule=LatencyJitterConfigSchedule(duration=schedule.duration, period=schedule.period)
        )

    async def set(self, config: Optional[LatencyJitterConfigMain] =None, constant_delay: Optional[int] = None, duration: Optional[int] = None, period: Optional[int] = None) -> None:
        if not config:
            config = LatencyJitterConfigMain(
                distribution=LatencyJitterConfigDistribution(constant_delay=constant_delay),
                schedule=LatencyJitterConfigSchedule(duration=duration, period=period),
            )

        if config.distribution.constant_delay:
            await self.impairment.distribution.constant_delay.set(config.distribution.constant_delay)

        # if config.schedule:
        #     if config.schedule.duration or config.schedule.period:
        #         await self.impairment.schedule.set(config.schedule.duration or 1, config.schedule.period or 0)

    async def enable(self, b: bool) -> None:
        await self.impairment.enable.set(enums.OnOff(b))


class DropHandler:
    def __init__(self, impairment: "CDropImpairment"):
        self.impairment = impairment

    async def set(self):
        await self.impairment.distribution.fixed_burst.set(burst_size=5)
        await self.impairment.schedule.set(1, 5)

    async def enable(self, b: bool) -> None:
        await self.impairment.enable.set(enums.OnOff(b))


class ShadowFilterConfiguratorBasic:
    def __init__(self, filter_: "FilterDefinitionShadow", basic_mode: "ModeBasic"):
        self.filter = filter_
        self.basic_mode = basic_mode

    async def get(self) -> ShadowFilterConfigBasic:
        settings, src_addr, dest_addr, l2plus = await asyncio.gather(*(
            self.basic_mode.ethernet.settings.get(),
            self.basic_mode.ethernet.src_address.get(),
            self.basic_mode.ethernet.dest_address.get(),
            self.basic_mode.l2plus_use.get(),

        ))
        ethernet = ShadowFilterConfigBasicEthernet(
            use=enums.FilterUse(settings.use),
            action=enums.InfoAction(settings.action),
            use_src_addr=enums.OnOff(src_addr.use),
            value_src_addr=src_addr.value,
            mask_src_addr=src_addr.mask,
            use_dest_addr=enums.OnOff(dest_addr.use),
            value_dest_addr=dest_addr.value,
            mask_dest_addr=dest_addr.mask,

        )
        config = ShadowFilterConfigBasic(
            ethernet=ethernet,
            l2plus_use=enums.L2PlusPresent(l2plus.use),
        )
        return config


class ShadowFilterManager:
    def __init__(self, filter: "FilterDefinitionShadow"):
        self.filter = filter

    async def reset(self) -> None:
        await self.filter.initiating.set()

    async def set(self):
        await self.filter.initiating.set()
        filter = await self.filter.get_mode()
        # Set up the filter to impair frames with VLAN Tag = 20 (using command grouping)
        if isinstance(filter, misc.BasicImpairmentFlowFilter):
            await utils.apply(
                filter.ethernet.settings.set(use=enums.FilterUse.OFF, action=enums.InfoAction.INCLUDE),
                filter.ethernet.src_address.set(use=enums.OnOff.OFF, value="0x000000000000", mask="0xFFFFFFFFFFFF"),
                filter.ethernet.dest_address.set(use=enums.OnOff.OFF, value="0x000000000000", mask="0xFFFFFFFFFFFF"),
                filter.l2plus_use.set(use=enums.L2PlusPresent.VLAN1),
                filter.vlan.settings.set(use=enums.FilterUse.AND, action=enums.InfoAction.INCLUDE),
                filter.vlan.inner.tag.set(use=enums.OnOff.ON, value=20, mask="0x0FFF"),
                filter.vlan.inner.pcp.set(use=enums.OnOff.OFF, value=0, mask="0x07"),
                filter.vlan.outer.tag.set(use=enums.OnOff.OFF, value=20, mask="0x0FFF"),
                filter.vlan.outer.pcp.set(use=enums.OnOff.OFF, value=0, mask="0x07"),
            )

    async def use_basic_mode(self) -> "ShadowFilterConfiguratorBasic":
        await self.filter.use_basic_mode()
        mode = await self.filter.get_mode()
        if not isinstance(mode, ModeBasic):
            raise ValueError("Not base mode")
        return ShadowFilterConfiguratorBasic(self.filter, mode)

    async def enable(self, state: bool) -> None:
        await self.filter.enable.set(enums.OnOff(state))
        if state:
            await self.filter.apply.set()
