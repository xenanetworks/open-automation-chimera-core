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

from xoa_driver.internals.hli_v2.ports.port_l23.chimera.filter_definition.general import ModeBasic, ModeExtended

from .dataset import (
    TPLD_FILTERS_LENGTH,
    DropConfigMain,
    DistributionResponseValidator,
    InnerOuter,
    LatencyJitterConfigMain,
    Schedule,
    ShadowFilterConfigAnyField,
    ShadowFilterConfigBasic,
    ShadowFilterConfigEthernet,
    ShadowFilterConfigEthernetAddr,
    ShadowFilterConfigExtended,
    ShadowFilterConfigL2IPv4DSCP,
    ShadowFilterConfigL3IPv4,
    ShadowFilterConfigL2IPv4Addr,
    ShadowFilterConfigBasicIPv6DESTADDR,
    ShadowFilterConfigL3IPv6,
    ShadowFilterConfigBasicIPv6SRCADDR,
    ShadowFilterConfigL2MPLS,
    ShadowFilterConfigL2VLAN,
    ShadowFilterConfigL4TCP,
    ShadowFilterConfigTPLD,
    ShadowFilterConfigTPLDID,
    ShadowFilterLayer2,
    ShadowFilterLayer2Plus,
    ShadowFilterLayer3,
    ShadowFilterLayer4,
    ShadowFilterLayerAny,
    ShadowFilterLayerXena,
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


class ShadowFilterConfiguratorExtended:
    def __init__(self, filter_: "FilterDefinitionShadow", extended_mode: "ModeExtended"):
        self.shadow_filter = filter_
        self.extended_mode = extended_mode

    async def get(self) -> ShadowFilterConfigExtended:
        return ShadowFilterConfigExtended()


class ShadowFilterConfiguratorBasic:
    def __init__(self, filter_: "FilterDefinitionShadow", basic_mode: "ModeBasic"):
        self.shadow_filter = filter_
        self.basic_mode = basic_mode

    async def get(self) -> ShadowFilterConfigBasic:
        ethernet, src_addr, dest_addr, \
            l2, vlan, vlan_tag_inner, vlan_pcp_inner, vlan_tag_outer, vlan_pcp_outer, mpls, mpls_label, mpls_toc, \
            l3, ipv4, ipv4_src_addr, ipv4_dest_addr, ipv4_dscp, ipv6, ipv6_src_addr, ipv6_dest_addr, \
            tcp, tcp_src_port, tcp_dest_port, \
            tpld, *tpld_id_settings, \
            any_, any_field = await asyncio.gather(*(
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
                *(self.basic_mode.tpld.test_payload_filters_config[i].get() for i in range(TPLD_FILTERS_LENGTH)),

                self.basic_mode.any.settings.get(),
                self.basic_mode.any.config.get(),

            ))

        config_ethernet = ShadowFilterConfigEthernet(
            filter_use=enums.FilterUse(ethernet.use),
            match_action=enums.InfoAction(ethernet.action),
            src_addr=ShadowFilterConfigEthernetAddr(
                use=enums.OnOff(ipv4_dest_addr.use),
                value=ipv4_dest_addr.value,
                mask=ipv4_dest_addr.mask,
            ),
            dest_addr=ShadowFilterConfigEthernetAddr(
                use=enums.OnOff(ipv4_dest_addr.use),
                value=ipv4_dest_addr.value,
                mask=ipv4_dest_addr.mask,
            ),
        )

        tag_inner = generate_inner_outer(vlan_tag_inner)
        tag_outer = generate_inner_outer(vlan_tag_outer)
        pcp_inner = generate_inner_outer(vlan_pcp_inner)
        pcp_outer = generate_inner_outer(vlan_pcp_outer)
        config_vlan = ShadowFilterConfigL2VLAN(
            filter_use=enums.FilterUse(vlan.use),
            match_action=enums.InfoAction(vlan.action),
            tag_inner=tag_inner,
            tag_outer=tag_outer,
            pcp_inner=pcp_inner,
            pcp_outer=pcp_outer,
        )

        config_mpls_label = generate_inner_outer(mpls_label)
        config_mpls_toc = generate_inner_outer(mpls_toc)
        config_mpls = ShadowFilterConfigL2MPLS(
            filter_use=enums.FilterUse(mpls.use),
            match_action=enums.InfoAction(mpls.action),
            label=config_mpls_label,
            toc=config_mpls_toc,
        )

        config_ipv4 = ShadowFilterConfigL3IPv4(
            filter_use=enums.FilterUse(ipv4.use),
            match_action=enums.InfoAction(ipv4.action),
            src_addr=ShadowFilterConfigL2IPv4Addr(
                use=enums.OnOff(ipv4_src_addr.use),
                value=ipv4_src_addr.value,
                mask=ipv4_src_addr.mask,
            ),
            dest_addr=ShadowFilterConfigL2IPv4Addr(
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
            filter_use=enums.FilterUse(ipv6.use),
            match_action=enums.InfoAction(ipv6.action),
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
            filter_use=enums.FilterUse(tcp.use),
            match_action=enums.InfoAction(tcp.action),
            src_port=generate_inner_outer(tcp_src_port),
            dest_port=generate_inner_outer(tcp_dest_port),
        )
        use_l2plus = ShadowFilterLayer2Plus(present=l2.use, vlan=config_vlan, mpls=config_mpls)
        use_l3 = ShadowFilterLayer3(present=l3.use, ipv4=config_ipv4, ipv6=config_ipv6)
        use_l4 = ShadowFilterLayer4(tcp=config_tcp)

        tpld_id_configs = []
        for i, setting in enumerate(tpld_id_settings):
            tpld_id_configs.append(ShadowFilterConfigTPLDID(filter_index=i, tpld_id=setting.id, use=setting.use))
        tpld_id_configs = *tpld_id_configs,
        use_xena = ShadowFilterLayerXena(tpld=ShadowFilterConfigTPLD(filter_use=enums.FilterUse(tpld.use), match_action=enums.InfoAction(tpld.action), configs=tpld_id_configs))

        config_any = ShadowFilterLayerAny(
            filter_use=enums.FilterUse(any_.use),
            match_action=enums.InfoAction(any_.action),
            any_field=ShadowFilterConfigAnyField(position=any_field.posittion, value=any_field.value, mask=any_field.mask),
        )
        config = ShadowFilterConfigBasic(
            layer_2=ShadowFilterLayer2(ethernet=config_ethernet),
            layer_2_plus=use_l2plus,
            layer_3=use_l3,
            layer_4=use_l4,
            layer_xena=use_xena,
            layer_any=config_any,
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
            self.basic_mode.l2plus_use.set(use=config.layer_2_plus.present),
            self.basic_mode.l3_use.set(use=config.layer_3.present),
        ]

        if config.layer_2_plus.present in (enums.L2PlusPresent.VLAN1, enums.L2PlusPresent.VLAN2):
            coroutines.extend([
                self.basic_mode.vlan.settings.set(use=config.layer_2_plus.vlan.filter_use, action=config.layer_2_plus.vlan.match_action),
                self.basic_mode.vlan.inner.tag.set(
                    use=config.layer_2_plus.vlan.tag_inner.use,
                    value=config.layer_2_plus.vlan.tag_inner.value,
                    mask=f"0x{config.layer_2_plus.vlan.tag_inner.mask}",
                ),
                self.basic_mode.vlan.inner.pcp.set(
                    use=config.layer_2_plus.vlan.pcp_inner.use,
                    value=config.layer_2_plus.vlan.pcp_inner.value,
                    mask=f"0x{config.layer_2_plus.vlan.pcp_inner.mask}",
                ),
                self.basic_mode.vlan.outer.tag.set(
                    use=config.layer_2_plus.vlan.tag_outer.use,
                    value=config.layer_2_plus.vlan.tag_outer.value,
                    mask=f"0x{config.layer_2_plus.vlan.tag_outer.mask}",
                ),
                self.basic_mode.vlan.outer.pcp.set(
                    use=config.layer_2_plus.vlan.pcp_outer.use,
                    value=config.layer_2_plus.vlan.pcp_outer.value,
                    mask=f"0x{config.layer_2_plus.vlan.pcp_outer.mask}",
                ),
            ])

        elif config.layer_2_plus.present == enums.L2PlusPresent.MPLS:
            coroutines.extend([
                self.basic_mode.mpls.settings.set(use=config.layer_2_plus.mpls.filter_use, action=config.layer_2_plus.mpls.match_action),
                self.basic_mode.mpls.label.set(
                    use=config.layer_2_plus.mpls.label.use,
                    value=config.layer_2_plus.mpls.label.value,
                    mask=f"0x{config.layer_2_plus.mpls.label.mask}",
                ),
                self.basic_mode.mpls.toc.set(
                    use=config.layer_2_plus.mpls.toc.use,
                    value=config.layer_2_plus.mpls.toc.value,
                    mask=f"0x{config.layer_2_plus.mpls.toc.mask}",
                ),
            ])

        if config.layer_3 == enums.L3PlusPresent.IP4:
            coroutines.extend([
                self.basic_mode.ip.v4.settings.set(use=config.layer_3.ipv4.filter_use, action=config.layer_3.ipv4.match_action),
                self.basic_mode.ip.v4.src_address.set(
                    use=config.layer_3.ipv4.src_addr.use,
                    value=config.layer_3.ipv4.src_addr.value,
                    mask=config.layer_3.ipv4.src_addr.mask,
                ),
                self.basic_mode.ip.v4.dest_address.set(
                    use=config.layer_3.ipv4.dest_addr.use,
                    value=config.layer_3.ipv4.dest_addr.value,
                    mask=config.layer_3.ipv4.dest_addr.mask,
                ),
            ])

        elif config.layer_3 == enums.L3PlusPresent.IP6:
            coroutines.extend([
                self.basic_mode.ip.v6.settings.set(use=config.layer_3.ipv6.filter_use, action=config.layer_3.ipv6.match_action),
                self.basic_mode.ip.v6.src_address.set(
                    use=config.layer_3.ipv6.src_addr.use,
                    value=config.layer_3.ipv6.src_addr.value,
                    mask=config.layer_3.ipv6.src_addr.mask,
                ),
                self.basic_mode.ip.v6.dest_address.set(
                    use=config.layer_3.ipv6.dest_addr.use,
                    value=config.layer_3.ipv6.dest_addr.value,
                    mask=config.layer_3.ipv6.dest_addr.mask,
                ),
            ])

        if not config.layer_4.tcp.is_off:
            logger.debug(config.layer_4.tcp)
            coroutines.extend([
                self.basic_mode.tcp.settings.set(use=config.layer_4.tcp.filter_use, action=config.layer_4.tcp.match_action),
                self.basic_mode.tcp.src_port.set(
                    use=config.layer_4.tcp.src_port.use,
                    value=config.layer_4.tcp.src_port.value,
                    mask=f"0x{config.layer_4.tcp.src_port.mask}",
                ),
                self.basic_mode.tcp.dest_port.set(
                    use=config.layer_4.tcp.dest_port.use,
                    value=config.layer_4.tcp.dest_port.value,
                    mask=f"0x{config.layer_4.tcp.dest_port.mask}",
                ),
            ])
        elif not config.layer_4.udp.is_off:
            coroutines.extend([
                self.basic_mode.udp.settings.set(use=config.layer_4.udp.filter_use, action=config.layer_4.udp.match_action),
                self.basic_mode.udp.src_port.set(
                    use=config.layer_4.udp.src_port.use,
                    value=config.layer_4.udp.src_port.value,
                    mask=f"0x{config.layer_4.udp.src_port.mask}",
                ),
                self.basic_mode.udp.dest_port.set(
                    use=config.layer_4.udp.dest_port.use,
                    value=config.layer_4.udp.dest_port.value,
                    mask=f"0x{config.layer_4.udp.dest_port.mask}",
                ),
            ])

        if not config.layer_xena.tpld.is_off:
            coroutines.extend([
                self.basic_mode.tpld.settings.set(use=config.layer_xena.tpld.filter_use, action=config.layer_xena.tpld.match_action),
                *(
                    tpld_filter.set(use=config.layer_xena.tpld.configs[i].use, id=config.layer_xena.tpld.configs[i].tpld_id)
                    for i, tpld_filter in enumerate(self.basic_mode.tpld.test_payload_filters_config)
                ),

            ])
        if not config.layer_any.any_field.is_off:
            coroutines.extend([
                self.basic_mode.any.settings.set(use=config.layer_any.any_field.filter_use, action=config.layer_any.any_field.match_action),
                self.basic_mode.any.config.set(
                    position=config.layer_any.any_field.position,
                    value=config.layer_any.any_field.value,
                    mask=config.layer_any.any_field.mask,
                )
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

    async def use_extended_mode(self) -> "ShadowFilterConfiguratorExtended":
        await self.filter.use_extended_mode()
        mode = await self.filter.get_mode()
        if not isinstance(mode, ModeExtended):
            raise ValueError("Not extended mode")
        return ShadowFilterConfiguratorExtended(self.filter, mode)

    async def enable(self, state: bool) -> None:
        await self.filter.enable.set(enums.OnOff(state))
        if state:
            await self.filter.apply.set()
