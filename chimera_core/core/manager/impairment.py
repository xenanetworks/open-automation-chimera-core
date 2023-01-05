import asyncio
from typing import (
    TYPE_CHECKING,
    Dict,
    Generic,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeVar,
    Union,
    Any,
)

from loguru import logger
from xoa_driver import utils, enums
from xoa_driver.v2 import misc
from xoa_driver.lli import commands

from xoa_driver.internals.hli_v2.ports.port_l23.chimera.filter_definition.general import ModeBasic

from .dataset import (
    DropConfigMain,
    DistributionResponseValidator,
    InnerOuter,
    LatencyJitterConfigMain,
    Schedule,
    ShadowFilterConfigBasic,
    ShadowFilterConfigBasicEthernet,
    ShadowFilterConfigL2IPv4DESTADDR,
    ShadowFilterConfigL2IPv4DSCP,
    ShadowFilterConfigL3IPv4,
    ShadowFilterConfigL2IPv4SRCADDR,
    ShadowFilterConfigBasicIPv6DESTADDR,
    ShadowFilterConfigL3IPv6,
    ShadowFilterConfigBasicIPv6SRCADDR,
    ShadowFilterConfigL2MPLS,
    ShadowFilterConfigL2VLAN,
    ShadowFilterConfigL4TCP,
    ShadowFilterConfigTPLD,
    ShadowFilterConfigTPLDID,
    UseL2Plus,
    UseL3,
    UseL4,
    UseXena,
)

from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import CLatencyJitterImpairment, CDropImpairment
from xoa_driver.internals.hli_v2.ports.port_l23.chimera.filter_definition.shadow import FilterDefinitionShadow


T = TypeVar('T', CLatencyJitterImpairment, CDropImpairment)


class ImpairmentConfiguratorBase(Generic[T]):
    def __init__(self, impairment: T):
        self.impairment = impairment

    async def _get_enable_and_schedule(self) -> Tuple[commands.PED_ENABLE.GetDataAttr, commands.PED_SCHEDULE.GetDataAttr]:
        enable, schedule = await asyncio.gather(*(
            self.impairment.enable.get(),
            self.impairment.schedule.get(),
        ))
        return enable, schedule

    async def enable(self, state: bool) -> None:
        await self.impairment.enable.set(enums.OnOff(state))


class LatencyJitterConfigurator(ImpairmentConfiguratorBase[CLatencyJitterImpairment]):
    async def get(self) -> LatencyJitterConfigMain:
        enable, schedule = await self._get_enable_and_schedule()

        # distributions = await asyncio.gather(*(
        #     self.impairment.distribution.constant_delay.get(),
        #     self.impairment.distribution.accumulate_and_burst.get(),
        #     self.impairment.distribution.step.get(),
        #     self.impairment.distribution.uniform.get(),
        #     self.impairment.distribution.gaussian.get(),
        #     self.impairment.distribution.poison.get(),
        #     self.impairment.distribution.gamma.get(),
        #     self.impairment.distribution.custom.get(),
        # ), return_exceptions=True)

        config = LatencyJitterConfigMain(
            enable=enums.OnOff(enable.action),
            schedule=Schedule(duration=schedule.duration, period=schedule.period),
        )
        commands = config.get_distribution_commands(self.impairment)
        logger.debug(commands)
        responses = dict(zip(commands.keys(), await asyncio.gather(*commands.values(), return_exceptions=True)))
        config.validate_response_and_load_value(responses)
        return config

    async def set(self, config: LatencyJitterConfigMain) -> None:
        await asyncio.gather(*(
            self.impairment.schedule.set(duration=config.schedule.duration, period=config.schedule.period),
            self.impairment.distribution.constant_delay.set(config.constant_delay.delay)
        ))


class DropConfigurator(ImpairmentConfiguratorBase[CDropImpairment]):
    def __init__(self, impairment: "CDropImpairment"):
        self.impairment = impairment

    async def get(self) -> DropConfigMain:
        enable, schedule = await self._get_enable_and_schedule()

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

    async def set(self, config: DropConfigMain):
        await asyncio.gather(*(
            self.impairment.schedule.set(duration=config.schedule.duration, period=config.schedule.period),
            self.impairment.distribution.fixed_burst.set(burst_size=config.fixed_burst.burst_size),
        ))


class PInnerOuterGetDataAttr(Protocol):
    use: Any
    value: int
    mask: str


def generate_inner_outer(attr: PInnerOuterGetDataAttr) -> InnerOuter:
    return InnerOuter(use=enums.OnOff(attr.use), value=attr.value, mask=attr.mask.replace('0x', ''))


class ShadowFilterConfiguratorBasic:
    def __init__(self, filter_: "FilterDefinitionShadow", basic_mode: "ModeBasic"):
        self.shadow_filter = filter_
        self.basic_mode = basic_mode

    async def get(self) -> ShadowFilterConfigBasic:
        ethernet, src_addr, dest_addr, \
            l2, vlan, vlan_tag_inner, vlan_pcp_inner, vlan_tag_outer, vlan_pcp_outer, mpls, mpls_label, mpls_toc, \
            l3, ipv4, ipv4_src_addr, ipv4_dest_addr, ipv4_dscp, ipv6, ipv6_src_addr, ipv6_dest_addr, \
            tcp, tcp_src_port, tcp_dest_port, \
            tpld, *tpld_id_settings = await asyncio.gather(*(
                self.basic_mode.ethernet.settings.get(),
                self.basic_mode.ethernet.src_address.get(),
                self.basic_mode.ethernet.dest_address.get(),

                self.basic_mode.l2plus_use.get(),
                self.basic_mode.vlan.settings.get(),
                self.basic_mode.vlan.inner.tag.get(),
                self.basic_mode.vlan.inner.pcp.get(),
                self.basic_mode.vlan.outer.tag.get(),
                self.basic_mode.vlan.outer.pcp.get(),
                self.basic_mode.mpls.settings.get(),
                self.basic_mode.mpls.label.get(),
                self.basic_mode.mpls.toc.get(),

                self.basic_mode.l3_use.get(),
                self.basic_mode.ip.v4.settings.get(),
                self.basic_mode.ip.v4.src_address.get(),
                self.basic_mode.ip.v4.dest_address.get(),
                self.basic_mode.ip.v4.dscp.get(),
                self.basic_mode.ip.v6.settings.get(),
                self.basic_mode.ip.v6.src_address.get(),
                self.basic_mode.ip.v6.dest_address.get(),

                self.basic_mode.tcp.settings.get(),
                self.basic_mode.tcp.src_port.get(),
                self.basic_mode.tcp.dest_port.get(),

                self.basic_mode.tpld.settings.get(),
                *(self.basic_mode.tpld.test_payload_filters_config[i].get() for i in range(16)),
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
        tag_inner = generate_inner_outer(vlan_tag_inner)
        tag_outer = generate_inner_outer(vlan_tag_outer)
        pcp_inner = generate_inner_outer(vlan_pcp_inner)
        pcp_outer = generate_inner_outer(vlan_pcp_outer)
        config_vlan = ShadowFilterConfigL2VLAN(
            use=enums.FilterUse(vlan.use),
            action=enums.InfoAction(vlan.action),
            tag_inner=tag_inner,
            tag_outer=tag_outer,
            pcp_inner=pcp_inner,
            pcp_outer=pcp_outer,
        )

        config_mpls_label = generate_inner_outer(mpls_label)
        config_mpls_toc = generate_inner_outer(mpls_toc)
        config_mpls = ShadowFilterConfigL2MPLS(
            use=enums.FilterUse(mpls.use),
            action=enums.InfoAction(mpls.action),
            label=config_mpls_label,
            toc=config_mpls_toc,
        )

        config_ipv4 = ShadowFilterConfigL3IPv4(
            use=enums.FilterUse(ipv4.use),
            action=enums.InfoAction(ipv4.action),
            src_addr=ShadowFilterConfigL2IPv4SRCADDR(
                use=enums.OnOff(ipv4_src_addr.use),
                value=ipv4_src_addr.value,
                mask=ipv4_src_addr.mask,
            ),
            dest_addr=ShadowFilterConfigL2IPv4DESTADDR(
                use=enums.OnOff(ipv4_dest_addr.use),
                value=ipv4_dest_addr.value,
                mask=ipv4_dest_addr.mask,
            ),
            dscp=ShadowFilterConfigL2IPv4DSCP(
                use=enums.OnOff(ipv4_dscp.use),
                value=ipv4_dscp.value,
                mask=ipv4_dscp.mask,
            ),
        )
        config_ipv6 = ShadowFilterConfigL3IPv6(
            use=enums.FilterUse(ipv6.use),
            action=enums.InfoAction(ipv6.action),
            src_addr=ShadowFilterConfigBasicIPv6SRCADDR(
                use=enums.OnOff(ipv6_src_addr.use),
                value=str(ipv6_src_addr.value),
                mask=ipv6_src_addr.mask,
            ),
            dest_addr=ShadowFilterConfigBasicIPv6DESTADDR(
                use=enums.OnOff(ipv6_dest_addr.use),
                value=str(ipv6_dest_addr.value),
                mask=ipv6_dest_addr.mask,
            ),
        )

        config_tcp = ShadowFilterConfigL4TCP(
            use=enums.FilterUse(tcp.use),
            action=enums.InfoAction(tcp.action),
            src_port=generate_inner_outer(tcp_src_port),
            dest_port=generate_inner_outer(tcp_dest_port),
        )
        use_l2plus = UseL2Plus(present=l2.use, vlan=config_vlan, mpls=config_mpls)
        use_l3 = UseL3(present=l3.use, ipv4=config_ipv4, ipv6=config_ipv6)
        use_l4 = UseL4(tcp=config_tcp)

        tpld_id_configs = []
        for i, setting in enumerate(tpld_id_settings):
            tpld_id_configs.append(ShadowFilterConfigTPLDID(filter_index=i, tpld_id=setting.id, use=setting.use))
        tpld_id_configs = *tpld_id_configs,
        use_xena = UseXena(tpld=ShadowFilterConfigTPLD(configs=tpld_id_configs))

        config = ShadowFilterConfigBasic(
            ethernet=config_ethernet,
            l2plus=use_l2plus,
            l3=use_l3,
            l4=use_l4,
            xena=use_xena,
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
            self.basic_mode.l2plus_use.set(use=config.l2plus.present),
            self.basic_mode.l3_use.set(use=config.l3.present),
        ]

        if config.l2plus.present in (enums.L2PlusPresent.VLAN1, enums.L2PlusPresent.VLAN2):
            coroutines.extend([
                self.basic_mode.vlan.settings.set(use=config.l2plus.vlan.use, action=config.l2plus.vlan.action),
                self.basic_mode.vlan.inner.tag.set(
                    use=config.l2plus.vlan.tag_inner.use,
                    value=config.l2plus.vlan.tag_inner.value,
                    mask=f"0x{config.l2plus.vlan.tag_inner.mask}",
                ),
                self.basic_mode.vlan.inner.pcp.set(
                    use=config.l2plus.vlan.pcp_inner.use,
                    value=config.l2plus.vlan.pcp_inner.value,
                    mask=f"0x{config.l2plus.vlan.pcp_inner.mask}",
                ),
                self.basic_mode.vlan.outer.tag.set(
                    use=config.l2plus.vlan.tag_outer.use,
                    value=config.l2plus.vlan.tag_outer.value,
                    mask=f"0x{config.l2plus.vlan.tag_outer.mask}",
                ),
                self.basic_mode.vlan.outer.pcp.set(
                    use=config.l2plus.vlan.pcp_outer.use,
                    value=config.l2plus.vlan.pcp_outer.value,
                    mask=f"0x{config.l2plus.vlan.pcp_outer.mask}",
                ),
            ])

        elif config.l2plus.present == enums.L2PlusPresent.MPLS:
            coroutines.extend([
                self.basic_mode.mpls.settings.set(use=config.l2plus.mpls.use, action=config.l2plus.mpls.action),
                self.basic_mode.mpls.label.set(
                    use=config.l2plus.mpls.label.use,
                    value=config.l2plus.mpls.label.value,
                    mask=f"0x{config.l2plus.mpls.label.mask}",
                ),
                self.basic_mode.mpls.toc.set(
                    use=config.l2plus.mpls.toc.use,
                    value=config.l2plus.mpls.toc.value,
                    mask=f"0x{config.l2plus.mpls.toc.mask}",
                ),
            ])

        if config.l3 == enums.L3PlusPresent.IP4:
            coroutines.extend([
                self.basic_mode.ip.v4.settings.set(use=config.l3.ipv4.use, action=config.l3.ipv4.action),
                self.basic_mode.ip.v4.src_address.set(
                    use=config.l3.ipv4.src_addr.use,
                    value=config.l3.ipv4.src_addr.value,
                    mask=config.l3.ipv4.src_addr.mask,
                ),
                self.basic_mode.ip.v4.dest_address.set(
                    use=config.l3.ipv4.dest_addr.use,
                    value=config.l3.ipv4.dest_addr.value,
                    mask=config.l3.ipv4.dest_addr.mask,
                ),
            ])

        elif config.l3 == enums.L3PlusPresent.IP6:
            coroutines.extend([
                self.basic_mode.ip.v6.settings.set(use=config.l3.ipv6.use, action=config.l3.ipv6.action),
                self.basic_mode.ip.v6.src_address.set(
                    use=config.l3.ipv6.src_addr.use,
                    value=config.l3.ipv6.src_addr.value,
                    mask=config.l3.ipv6.src_addr.mask,
                ),
                self.basic_mode.ip.v6.dest_address.set(
                    use=config.l3.ipv6.dest_addr.use,
                    value=config.l3.ipv6.dest_addr.value,
                    mask=config.l3.ipv6.dest_addr.mask,
                ),
            ])

        if not config.l4.tcp.is_off:
            logger.debug(config.l4.tcp)
            coroutines.extend([
                self.basic_mode.tcp.settings.set(use=config.l4.tcp.use, action=config.l4.tcp.action),
                self.basic_mode.tcp.src_port.set(
                    use=config.l4.tcp.src_port.use,
                    value=config.l4.tcp.src_port.value,
                    mask=f"0x{config.l4.tcp.src_port.mask}",
                ),
                self.basic_mode.tcp.dest_port.set(
                    use=config.l4.tcp.dest_port.use,
                    value=config.l4.tcp.dest_port.value,
                    mask=f"0x{config.l4.tcp.dest_port.mask}",
                ),
            ])
        elif not config.l4.udp.is_off:
            coroutines.extend([
                self.basic_mode.udp.settings.set(use=config.l4.udp.use, action=config.l4.udp.action),
                self.basic_mode.udp.src_port.set(
                    use=config.l4.udp.src_port.use,
                    value=config.l4.udp.src_port.value,
                    mask=f"0x{config.l4.udp.src_port.mask}",
                ),
                self.basic_mode.udp.dest_port.set(
                    use=config.l4.udp.dest_port.use,
                    value=config.l4.udp.dest_port.value,
                    mask=f"0x{config.l4.udp.dest_port.mask}",
                ),
            ])

        if not config.xena.tpld.is_off:
            coroutines.extend([
                self.basic_mode.tpld.settings.set(use=config.xena.tpld.use, action=config.xena.tpld.action),
            ])

        # await asyncio.gather(*coroutines)
        await utils.apply(*coroutines)


class ShadowFilterManager:
    def __init__(self, filter: "FilterDefinitionShadow"):
        self.filter = filter

    async def reset(self) -> None:
        await self.filter.initiating.set()

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
