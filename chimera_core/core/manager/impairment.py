import asyncio
from typing import TYPE_CHECKING, NamedTuple, Optional, Union, Any

from loguru import logger
from xoa_driver import utils, enums
from xoa_driver.v2 import misc

from xoa_driver.internals.hli_v2.ports.port_l23.chimera.filter_definition.general import ModeBasic

from .dataset import (
    DropConfigMain,
    DistributionResponseValidator,
    LatencyJitterConfigMain,
    Schedule,
    ShadowFilterConfigBasic,
    ShadowFilterConfigBasicEthernet,
    ShadowFilterConfigBasicIPv4DESTADDR,
    ShadowFilterConfigBasicIPv4DSCP,
    ShadowFilterConfigBasicIPv4Main,
    ShadowFilterConfigBasicIPv4SRCADDR,
    ShadowFilterConfigBasicIPv6DESTADDR,
    ShadowFilterConfigBasicIPv6Main,
    ShadowFilterConfigBasicIPv6SRCADDR,
    ShadowFilterConfigBasicVLAN,
)

if TYPE_CHECKING:
    from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import CLatencyJitterImpairment, CDropImpairment
    from xoa_driver.internals.hli_v2.ports.port_l23.chimera.filter_definition.shadow import FilterDefinitionShadow


class LatencyJitter:
    def __init__(self, impairment: "CLatencyJitterImpairment"):
        self.impairment = impairment

    async def get(self) -> LatencyJitterConfigMain:
        enable, schedule = await asyncio.gather(*(
            self.impairment.enable.get(),
            self.impairment.schedule.get(),
        ))

        return LatencyJitterConfigMain(
            enable=enable.action,

        )

    async def set(self, config: Optional[LatencyJitterConfigMain]) -> None:
        if config.constant_delay:
            await self.impairment.distribution.constant_delay.set(config.distribution.constant_delay)

        # if config.schedule:
        #     if config.schedule.duration or config.schedule.period:
        #         await self.impairment.schedule.set(config.schedule.duration or 1, config.schedule.period or 0)

    async def enable(self, b: bool) -> None:
        await self.impairment.enable.set(enums.OnOff(b))


class DropConfigurator:
    def __init__(self, impairment: "CDropImpairment"):
        self.impairment = impairment

    async def get(self) -> DropConfigMain:
        enable, schedule = await asyncio.gather(*(
            self.impairment.enable.get(),
            self.impairment.schedule.get(),
        ))

        distributions = await asyncio.gather(*(
            self.impairment.distribution.fixed_burst.get(),
            self.impairment.distribution.random.get(),
            self.impairment.distribution.fixed.get(),
            self.impairment.distribution.bit_error_rate.get(),
            self.impairment.distribution.ge.get(),
            self.impairment.distribution.uniform.get(),
            self.impairment.distribution.gaussian.get(),
            self.impairment.distribution.gamma.get(),
            self.impairment.distribution.poison.get(),
            self.impairment.distribution.custom.get(),
        ), return_exceptions=True)

        config = DropConfigMain(
            enable=enums.OnOff(enable.action),
            schedule=Schedule(duration=schedule.duration, period=schedule.period),
        )
        drv = DistributionResponseValidator(*distributions)
        config.load_value_from_validator(drv)
        return config

    async def set(self):
        pass

    async def enable(self, b: bool) -> None:
        await self.impairment.enable.set(enums.OnOff(b))


class ShadowFilterConfiguratorBasic:
    def __init__(self, filter_: "FilterDefinitionShadow", basic_mode: "ModeBasic"):
        self.shadow_filter = filter_
        self.basic_mode = basic_mode

    async def get(self) -> ShadowFilterConfigBasic:
        ethernet, src_addr, dest_addr, l2, vlan, vlan_tag_inner, vlan_pcp_inner, vlan_tag_outer, vlan_pcp_outer, \
            l3, ipv4, ipv4_src_addr, ipv4_dest_addr, ipv4_dscp, ipv6, ipv6_src_addr, ipv6_dest_addr = await asyncio.gather(*(
                self.basic_mode.ethernet.settings.get(),
                self.basic_mode.ethernet.src_address.get(),
                self.basic_mode.ethernet.dest_address.get(),
                self.basic_mode.l2plus_use.get(),
                self.basic_mode.vlan.settings.get(),
                self.basic_mode.vlan.inner.tag.get(),
                self.basic_mode.vlan.inner.pcp.get(),
                self.basic_mode.vlan.outer.tag.get(),
                self.basic_mode.vlan.outer.pcp.get(),
                self.basic_mode.l3_use.get(),
                self.basic_mode.ip.v4.settings.get(),
                self.basic_mode.ip.v4.src_address.get(),
                self.basic_mode.ip.v4.dest_address.get(),
                self.basic_mode.ip.v4.dscp.get(),
                self.basic_mode.ip.v6.settings.get(),
                self.basic_mode.ip.v6.src_address.get(),
                self.basic_mode.ip.v6.dest_address.get(),
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
            dscp=ShadowFilterConfigBasicIPv4DSCP(
                use=enums.OnOff(ipv4_dscp.use),
                value=ipv4_dscp.value,
                mask=ipv4_dscp.mask,
            ),
        )
        config_ipv6 = ShadowFilterConfigBasicIPv6Main(
            use=enums.FilterUse(ipv6.use),
            action=enums.InfoAction(ipv6.action),
            src_addr=ShadowFilterConfigBasicIPv6SRCADDR(
                use=enums.OnOff(ipv6_src_addr.use),
                value=ipv6_src_addr.value,
                mask=ipv6_src_addr.mask,
            ),
            dest_addr=ShadowFilterConfigBasicIPv6DESTADDR(
                use=enums.OnOff(ipv6_dest_addr.use),
                value=ipv6_dest_addr.value,
                mask=ipv6_dest_addr.mask,
            ),
        )

        config = ShadowFilterConfigBasic(
            ethernet=config_ethernet,
            use_l2plus=enums.L2PlusPresent(l2.use),
            vlan=config_vlan,
            use_l3=enums.L3PlusPresent(l3.use),
            ipv4=config_ipv4,
            ipv6=config_ipv6,
        )
        return config

    async def set(self, config: ShadowFilterConfigBasic) -> None:
        coroutines = [
            # self.basic_mode.ethernet.settings.set(config.ethernet.use, action=config.ethernet.action),
            # self.basic_mode.ethernet.src_address.set(
            #     use=config.ethernet.use_src_addr,
            #     value=config.ethernet.value_src_addr,
            #     mask=config.ethernet.mask_src_addr
            # ),
            # self.basic_mode.ethernet.dest_address.set(
            #     use=config.ethernet.use_dest_addr,
            #     value=config.ethernet.value_dest_addr,
            #     mask=config.ethernet.mask_dest_addr
            # ),
            self.basic_mode.l2plus_use.set(use=config.use_l2plus),
            self.basic_mode.l3_use.set(use=config.use_l3),
        ]

        if config.use_l2plus != enums.L2PlusPresent.NA:
            coroutines.extend([
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
            ])

        if config.use_l3 == enums.L3PlusPresent.IP4:
            coroutines.extend([
                self.basic_mode.ip.v4.settings.set(use=config.ipv4.use, action=config.ipv4.action),
                self.basic_mode.ip.v4.src_address.set(
                    use=config.ipv4.src_addr.use,
                    value=config.ipv4.src_addr.value,
                    mask=config.ipv4.src_addr.mask,
                ),
                self.basic_mode.ip.v4.dest_address.set(
                    use=config.ipv4.dest_addr.use,
                    value=config.ipv4.dest_addr.value,
                    mask=config.ipv4.dest_addr.mask,
                ),
            ])

        elif config.use_l3 == enums.L3PlusPresent.IP6:
            coroutines.extend([
                self.basic_mode.ip.v6.settings.set(use=config.ipv6.use, action=config.ipv6.action),
                self.basic_mode.ip.v6.src_address.set(
                    use=config.ipv6.src_addr.use,
                    value=config.ipv6.src_addr.value,
                    mask=config.ipv6.src_addr.mask,
                ),
                self.basic_mode.ip.v6.dest_address.set(
                    use=config.ipv6.dest_addr.use,
                    value=config.ipv6.dest_addr.value,
                    mask=config.ipv6.dest_addr.mask,
                ),
            ])
        # await asyncio.gather(*coroutines)
        await utils.apply(*coroutines)


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
