import asyncio
from itertools import chain

from loguru import logger
from xoa_driver import utils
from xoa_driver.internals.hli_v2.ports.port_l23.chimera.filter_definition.shadow import FilterDefinitionShadow
from xoa_driver.internals.hli_v2.ports.port_l23.chimera.filter_definition.general import ModeBasic

from chimera_core.types import enums
from chimera_core.core.manager.__dataset import GeneratorToken
from .__dataset import (
    TPLD_FILTERS_LENGTH,
    create_protocol_config_common,
    ShadowFilterConfigBasic,
    FilterProtocolEthernet,
    ShadowFilterConfigEthernetAddr,
    FilterProtocolL2VLAN,
    FilterProtocolL2MPLS,
    FilterProtocolL3IPv4,
    FilterProtocolL3IPv6,
    FilterProtocolL3IPv4Addr,
    FilterProtocolL3IPv4DSCP,
    ShadowFilterConfigBasicIPv6DESTADDR,
    ShadowFilterConfigBasicIPv6SRCADDR,
    FilterProtocolL4TCP,
    FilterLayer2Plus,
    FilterLayer2,
    FilterLayer3,
    FilterLayer4,
    FilterLayerAny,
    FilterLayerXena,
    FilterProtocolTPLD,
    ShadowFilterConfigTPLDID,
    FilterProtocolAnyField,
    ShadowFilterConfigVLANPCP,
    ShadowFilterConfigMPLSLabel,
    ShadowFilterConfigMPLSTOC,
    ShadowFilterConfigL4DestPort,
    ShadowFilterConfigL4SrcPort,
)


class ShadowFilterBasic:
    def __init__(self, shadow_filter_hli: "FilterDefinitionShadow", basic_mode_hli: "ModeBasic"):
        self.shadow_filter = shadow_filter_hli
        self.basic_mode = basic_mode_hli

    async def get(self) -> ShadowFilterConfigBasic:
        """Get the configuration of the shadow filter that is in basic mode

        :return: the configuration of the shadow filter that is in basic mode
        :rtype: ShadowFilterConfigBasic
        """
        ethernet, ethernet_src_addr, ethernet_dest_addr, \
            l2, vlan, vlan_tag_inner, vlan_pcp_inner, vlan_tag_outer, vlan_pcp_outer, mpls, mpls_label, mpls_toc, \
            l3, ipv4, ipv4_src_addr, ipv4_dest_addr, ipv4_dscp, ipv6, ipv6_src_addr, ipv6_dest_addr, \
            tcp, tcp_src_port, tcp_dest_port, \
            tpld, *tpld_id_settings, \
            any_setting, any_config = await asyncio.gather(*(
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

        config_ethernet = FilterProtocolEthernet(
            filter_use=ethernet.use,
            match_action=ethernet.action,
            src_addr=ShadowFilterConfigEthernetAddr(
                use=ethernet_src_addr.use,
                value=ethernet_src_addr.value,
                mask=ethernet_src_addr.mask,
            ),
            dest_addr=ShadowFilterConfigEthernetAddr(
                use=ethernet_dest_addr.use,
                value=ethernet_dest_addr.value,
                mask=ethernet_dest_addr.mask,
            ),
        )

        config_vlan = FilterProtocolL2VLAN(
            filter_use=vlan.use,
            match_action=vlan.action,
            tag_inner=create_protocol_config_common(vlan_tag_inner),
            tag_outer=create_protocol_config_common(vlan_tag_outer),
            pcp_inner=ShadowFilterConfigVLANPCP(value=vlan_pcp_inner.value, mask=vlan_pcp_inner.mask),
            pcp_outer=ShadowFilterConfigVLANPCP(value=vlan_pcp_outer.value, mask=vlan_pcp_outer.mask),
        )

        config_mpls = FilterProtocolL2MPLS(
            filter_use=mpls.use,
            match_action=mpls.action,
            label=ShadowFilterConfigMPLSLabel(value=mpls_label.value, mask=mpls_label.mask),
            toc=ShadowFilterConfigMPLSTOC(value=mpls_toc.value, mask=mpls_toc.mask),
        )

        config_ipv4 = FilterProtocolL3IPv4(
            match_action=ipv4.action,
            src_addr=FilterProtocolL3IPv4Addr(
                use=ipv4_src_addr.use,
                value=ipv4_src_addr.value,
                mask=ipv4_src_addr.mask,
            ),
            dest_addr=FilterProtocolL3IPv4Addr(
                use=ipv4_dest_addr.use,
                value=ipv4_dest_addr.value,
                mask=ipv4_dest_addr.mask,
            ),
            dscp=FilterProtocolL3IPv4DSCP(
                value=ipv4_dscp.value,
                mask=ipv4_dscp.mask,
            ),
        )
        config_ipv6 = FilterProtocolL3IPv6(
            match_action=ipv6.action,
            src_addr=ShadowFilterConfigBasicIPv6SRCADDR(
                use=ipv6_src_addr.use,
                value=ipv6_src_addr.value,
                mask=ipv6_src_addr.mask,
            ),
            dest_addr=ShadowFilterConfigBasicIPv6DESTADDR(
                use=ipv6_dest_addr.use,
                value=ipv6_dest_addr.value,
                mask=ipv6_dest_addr.mask,
            ),
        )

        config_tcp = FilterProtocolL4TCP(
            filter_use=tcp.use,
            match_action=tcp.action,
            src_port=ShadowFilterConfigL4SrcPort(value=tcp_src_port.value, mask=tcp_src_port.mask),
            dest_port=ShadowFilterConfigL4DestPort(value=tcp_dest_port.value, mask=tcp_dest_port.mask),
        )
        use_l2plus = FilterLayer2Plus(present=l2.use, vlan=config_vlan, mpls=config_mpls)
        use_l3 = FilterLayer3(present=l3.use, ipv4=config_ipv4, ipv6=config_ipv6)
        use_l4 = FilterLayer4(tcp=config_tcp)

        tpld_id_configs = []
        for i, setting in enumerate(tpld_id_settings):
            tpld_id_configs.append(ShadowFilterConfigTPLDID(filter_index=i, tpld_id=setting.id, use=setting.use))
        use_xena = FilterLayerXena(
            tpld=FilterProtocolTPLD(
                match_action=tpld.action,
                _configs=tpld_id_configs,
            ))

        config_any = FilterLayerAny(
            filter_use=any_setting.use,
            match_action=any_setting.action,
            any_field=FilterProtocolAnyField(position=any_config.position, value=any_config.value, mask=any_config.mask),
        )
        basic_config = ShadowFilterConfigBasic(
            layer_2=FilterLayer2(ethernet=config_ethernet),
            layer_2_plus=use_l2plus,
            layer_3=use_l3,
            layer_4=use_l4,
            layer_xena=use_xena,
            layer_any=config_any,
        )
        return basic_config

    def set_layer_2(self, config: ShadowFilterConfigBasic) -> GeneratorToken:
        if config.layer_2.ethernet.is_off:
            return None
        yield self.basic_mode.ethernet.settings.set(config.layer_2.ethernet.filter_use, action=config.layer_2.ethernet.match_action)
        yield self.basic_mode.ethernet.src_address.set(
            use=config.layer_2.ethernet.src_addr.use,
            value=config.layer_2.ethernet.src_addr.value,
            mask=config.layer_2.ethernet.src_addr.mask,
        )
        yield self.basic_mode.ethernet.dest_address.set(
            use=config.layer_2.ethernet.dest_addr.use,
            value=config.layer_2.ethernet.dest_addr.value,
            mask=config.layer_2.ethernet.dest_addr.mask,
        )

    def set_layer_2_plus(self, config: ShadowFilterConfigBasic) -> GeneratorToken:
        if config.layer_2_plus.present == enums.L2PlusPresent.NA:
            return
        yield self.basic_mode.l2plus_use.set(use=config.layer_2_plus.present)
        if config.layer_2_plus.present in (enums.L2PlusPresent.VLAN1, enums.L2PlusPresent.VLAN2):
            yield self.basic_mode.vlan.settings.set(use=config.layer_2_plus.vlan.filter_use, action=config.layer_2_plus.vlan.match_action)
            yield self.basic_mode.vlan.inner.tag.set(
                use=config.layer_2_plus.vlan.tag_inner.use,
                value=config.layer_2_plus.vlan.tag_inner.value,
                mask=config.layer_2_plus.vlan.tag_inner.mask,
            )
            yield self.basic_mode.vlan.inner.pcp.set(
                use=config.layer_2_plus.vlan.pcp_inner.use,
                value=config.layer_2_plus.vlan.pcp_inner.value,
                mask=config.layer_2_plus.vlan.pcp_inner.mask,
            )
            yield self.basic_mode.vlan.outer.tag.set(
                use=config.layer_2_plus.vlan.tag_outer.use,
                value=config.layer_2_plus.vlan.tag_outer.value,
                mask=config.layer_2_plus.vlan.tag_outer.mask,
            )
            yield self.basic_mode.vlan.outer.pcp.set(
                use=config.layer_2_plus.vlan.pcp_outer.use,
                value=config.layer_2_plus.vlan.pcp_outer.value,
                mask=config.layer_2_plus.vlan.pcp_outer.mask,
            )

        elif config.layer_2_plus.present == enums.L2PlusPresent.MPLS:
            yield self.basic_mode.mpls.settings.set(use=config.layer_2_plus.mpls.filter_use, action=config.layer_2_plus.mpls.match_action)
            yield self.basic_mode.mpls.label.set(
                use=config.layer_2_plus.mpls.label.use,
                value=config.layer_2_plus.mpls.label.value,
                mask=config.layer_2_plus.mpls.label.mask,
            )
            yield self.basic_mode.mpls.toc.set(
                use=config.layer_2_plus.mpls.toc.use,
                value=config.layer_2_plus.mpls.toc.value,
                mask=config.layer_2_plus.mpls.toc.mask,
            )

    def set_layer_3(self, config: ShadowFilterConfigBasic) -> GeneratorToken:
        yield self.basic_mode.l3_use.set(use=config.layer_3.present)
        if config.layer_3 == enums.L3PlusPresent.IP4:
            yield self.basic_mode.ip.v4.settings.set(use=config.layer_3.ipv4.filter_use, action=config.layer_3.ipv4.match_action)
            yield self.basic_mode.ip.v4.src_address.set(
                use=config.layer_3.ipv4.src_addr.use,
                value=config.layer_3.ipv4.src_addr.value,
                mask=config.layer_3.ipv4.src_addr.mask,
            )
            yield self.basic_mode.ip.v4.dest_address.set(
                use=config.layer_3.ipv4.dest_addr.use,
                value=config.layer_3.ipv4.dest_addr.value,
                mask=config.layer_3.ipv4.dest_addr.mask,
            )

        elif config.layer_3 == enums.L3PlusPresent.IP6:
            yield self.basic_mode.ip.v6.settings.set(use=config.layer_3.ipv6.filter_use, action=config.layer_3.ipv6.match_action)
            yield self.basic_mode.ip.v6.src_address.set(
                use=config.layer_3.ipv6.src_addr.use,
                value=config.layer_3.ipv6.src_addr.value,
                mask=config.layer_3.ipv6.src_addr.mask,
            )
            yield self.basic_mode.ip.v6.dest_address.set(
                use=config.layer_3.ipv6.dest_addr.use,
                value=config.layer_3.ipv6.dest_addr.value,
                mask=config.layer_3.ipv6.dest_addr.mask,
            )

    def set_layer_4(self, config: ShadowFilterConfigBasic) -> GeneratorToken:
        if not config.layer_4.tcp.is_off:
            yield self.basic_mode.tcp.settings.set(use=config.layer_4.tcp.filter_use, action=config.layer_4.tcp.match_action)
            yield self.basic_mode.tcp.src_port.set(
                use=config.layer_4.tcp.src_port.use,
                value=config.layer_4.tcp.src_port.value,
                mask=config.layer_4.tcp.src_port.mask,
            )
            yield self.basic_mode.tcp.dest_port.set(
                use=config.layer_4.tcp.dest_port.use,
                value=config.layer_4.tcp.dest_port.value,
                mask=config.layer_4.tcp.dest_port.mask,
            )
        elif not config.layer_4.udp.is_off:
            yield self.basic_mode.udp.settings.set(use=config.layer_4.udp.filter_use, action=config.layer_4.udp.match_action)
            yield self.basic_mode.udp.src_port.set(
                use=config.layer_4.udp.src_port.use,
                value=config.layer_4.udp.src_port.value,
                mask=config.layer_4.udp.src_port.mask,
            )
            yield self.basic_mode.udp.dest_port.set(
                use=config.layer_4.udp.dest_port.use,
                value=config.layer_4.udp.dest_port.value,
                mask=config.layer_4.udp.dest_port.mask,
            )

    def set_layer_xena(self, config: ShadowFilterConfigBasic) -> GeneratorToken:
        yield self.basic_mode.tpld.settings.set(action=config.layer_xena.tpld.match_action)
        for i, tpld_filter in enumerate(self.basic_mode.tpld.test_payload_filters_config):
            yield tpld_filter.set(use=config.layer_xena.tpld._configs[i].use, id=config.layer_xena.tpld._configs[i].tpld_id)

    def set_layer_any(self, config: ShadowFilterConfigBasic) -> GeneratorToken:
        if not config.layer_any.any_field.is_off:
            yield self.basic_mode.any.settings.set(use=config.layer_any.any_field.filter_use, action=config.layer_any.any_field.match_action)
            yield self.basic_mode.any.config.set(
                position=config.layer_any.any_field.position,
                value=config.layer_any.any_field.value,
                mask=config.layer_any.any_field.mask,
            )

    async def set(self, config: ShadowFilterConfigBasic) -> None:
        """Set the configuration of the shadow filter that is in basic mode

        :param config: the configuration of the shadow filter that is in basic mode
        :type config: ShadowFilterConfigBasic
        """
        await utils.apply(
            *chain(
                self.set_layer_2(config),
                self.set_layer_2_plus(config),
                self.set_layer_3(config),
                self.set_layer_4(config),
                self.set_layer_xena(config),
                self.set_layer_any(config),
            ),
            return_exceptions=False,
        )