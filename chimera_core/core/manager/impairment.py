import asyncio
from typing import TYPE_CHECKING, Optional

from loguru import logger
from xoa_driver import utils, enums
from xoa_driver.v2 import misc

from xoa_driver.internals.hli_v2.ports.port_l23.chimera.filter_definition.general import ModeBasic

from .dataset import (
    LatencyJitterConfigDistribution,
    LatencyJitterConfigMain,
    LatencyJitterConfigSchedule,
    ShadowFilterConfigBasic,
    ShadowFilterConfigBasicEthernet,
    ShadowFilterConfigBasicIPv4DESTADDR,
    ShadowFilterConfigBasicIPv4Main,
    ShadowFilterConfigBasicIPv4SRCADDR,
    ShadowFilterConfigBasicVLAN,
)

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

    async def set(self, config: Optional[LatencyJitterConfigMain]) -> None:
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
        self.shadow_filter = filter_
        self.basic_mode = basic_mode

    async def get(self) -> ShadowFilterConfigBasic:
        ethernet, src_addr, dest_addr, l2plus, vlan, vlan_tag_inner, vlan_pcp_inner, vlan_tag_outer, vlan_pcp_outer, \
            ipv4, ipv4_src_addr, ipv4_dest_addr = await asyncio.gather(*(
                self.basic_mode.ethernet.settings.get(),
                self.basic_mode.ethernet.src_address.get(),
                self.basic_mode.ethernet.dest_address.get(),
                self.basic_mode.l2plus_use.get(),
                self.basic_mode.vlan.settings.get(),
                self.basic_mode.vlan.inner.tag.get(),
                self.basic_mode.vlan.inner.pcp.get(),
                self.basic_mode.vlan.outer.tag.get(),
                self.basic_mode.vlan.outer.pcp.get(),
                self.basic_mode.ip.v4.settings.get(),
                self.basic_mode.ip.v4.src_address.get(),
                self.basic_mode.ip.v4.dest_address.get(),
            ))

        config_ethernet = ShadowFilterConfigBasicEthernet(
            use=enums.FilterUse(ethernet.use),
            action=enums.InfoAction(ethernet.action),
            use_src_addr=enums.OnOff(src_addr.use),
            value_src_addr=src_addr.value,
            mask_src_addr=src_addr.mask,
            use_dest_addr=enums.OnOff(dest_addr.use),
            value_dest_addr=dest_addr.value,
            mask_dest_addr=dest_addr.mask,

        )
        config_vlan = ShadowFilterConfigBasicVLAN(
            use=enums.FilterUse(vlan.use),
            action=enums.InfoAction(vlan.action),

            use_tag_inner=enums.OnOff(vlan_tag_inner.use),
            value_tag_inner=vlan_tag_inner.value,
            mask_tag_inner=vlan_tag_inner.mask,

            use_pcp_inner=enums.OnOff(vlan_pcp_inner.use),
            value_pcp_inner=vlan_pcp_inner.value,
            mask_pcp_inner=vlan_pcp_inner.mask,

            use_tag_outer=enums.OnOff(vlan_tag_outer.use),
            value_tag_outer=vlan_tag_outer.value,
            mask_tag_outer=vlan_tag_outer.mask,

            use_pcp_outer=enums.OnOff(vlan_pcp_outer.use),
            value_pcp_outer=vlan_pcp_outer.value,
            mask_pcp_outer=vlan_pcp_outer.mask,

        )
        config_ipv4 = ShadowFilterConfigBasicIPv4Main(
            use=enums.FilterUse(ipv4.use),
            action=enums.InfoAction(ipv4.action),
            src_addr=ShadowFilterConfigBasicIPv4SRCADDR(
                use=enums.OnOff(ipv4_src_addr.use),
                value=ipv4_src_addr.value,
                mask=ipv4_src_addr.mask,
            ),
            dest_addr=ShadowFilterConfigBasicIPv4DESTADDR(
                use=enums.OnOff(ipv4_dest_addr.use),
                value=ipv4_dest_addr.value,
                mask=ipv4_dest_addr.mask,
            ),
        )

        config = ShadowFilterConfigBasic(
            ethernet=config_ethernet,
            l2plus_use=enums.L2PlusPresent(l2plus.use),
            vlan=config_vlan,
            ipv4=config_ipv4,
        )
        return config

    async def set(self, config: ShadowFilterConfigBasic) -> None:
        logger.debug(config.vlan)
        coroutines = (
            self.basic_mode.ethernet.settings.set(config.ethernet.use, action=config.ethernet.action),
            self.basic_mode.ethernet.src_address.set(
                use=config.ethernet.use_src_addr,
                value=config.ethernet.value_src_addr,
                mask=config.ethernet.mask_src_addr
            ),
            self.basic_mode.ethernet.dest_address.set(
                use=config.ethernet.use_dest_addr,
                value=config.ethernet.value_dest_addr,
                mask=config.ethernet.mask_dest_addr
            ),
            self.basic_mode.l2plus_use.set(use=config.l2plus_use),
            self.basic_mode.vlan.settings.set(use=config.vlan.use, action=config.vlan.action),
            self.basic_mode.vlan.inner.tag.set(
                use=config.vlan.use_tag_inner,
                value=config.vlan.value_tag_inner,
                mask=config.vlan.mask_tag_inner
            ),
            self.basic_mode.vlan.inner.pcp.set(
                use=config.vlan.use_pcp_inner,
                value=config.vlan.value_pcp_inner,
                mask=config.vlan.mask_pcp_inner
            ),
            self.basic_mode.vlan.outer.tag.set(
                use=config.vlan.use_tag_outer,
                value=config.vlan.value_tag_outer,
                mask=config.vlan.mask_tag_outer,
            ),
            self.basic_mode.vlan.outer.pcp.set(
                use=config.vlan.use_pcp_outer,
                value=config.vlan.value_pcp_outer,
                mask=config.vlan.mask_pcp_outer,
            ),
        )
        await asyncio.gather(*coroutines)


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
