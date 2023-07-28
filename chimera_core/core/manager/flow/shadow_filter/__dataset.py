import ipaddress
from dataclasses import dataclass, field
from typing import Any, List, Protocol, Tuple

from xoa_driver.v2.misc import Hex

from chimera_core.types import enums


FFF_HEX = 'FFF'
TPLD_FILTERS_LENGTH = 16


class PInnerOuterGetDataAttr(Protocol):
    use: Any
    value: int
    mask: Hex


@dataclass
class ProtocolConfigCommon:
    use: enums.OnOff = enums.OnOff.OFF
    mask: Hex = Hex('FFF')
    value: int = 0

    def off(self, value: int = 0, mask: Hex = Hex('0FFF')) -> None:
        """Disable the match on this field

        :param value: value of the field, defaults to 0
        :type value: int, optional
        :param mask: value of the mask, defaults to 0FFF
        :type mask: Hex, optional
        """
        self.use = enums.OnOff.OFF
        self.value = value
        self.mask = mask

    def on(self, value: int = 0, mask: Hex = Hex('FFF')) -> None:
        """Enable th match on this field

        :param value: value of the field, defaults to 0
        :type value: int, optional
        :param mask: value of the mask, defaults to 0FFF
        :type mask: Hex, optional
        """
        self.use = enums.OnOff.ON
        self.value = value
        self.mask = mask


def create_protocol_config_common(attr: PInnerOuterGetDataAttr) -> ProtocolConfigCommon:
    return ProtocolConfigCommon(use=attr.use, value=attr.value, mask=Hex(attr.mask.replace('0x', '')))


@dataclass
class FilterConfigCommon:
    filter_use: enums.FilterUse = enums.FilterUse.OFF
    match_action: enums.InfoAction = enums.InfoAction.INCLUDE

    @property
    def is_off(self) -> bool:
        """Check whether the subfilter is off

        :return: whether the subfilter is off
        :rtype: bool
        """
        return self.filter_use == enums.FilterUse.OFF

    def include(self) -> None:
        """Use INCLUDE for match operation, AND for filter
        """
        self.filter_use = enums.FilterUse.AND
        self.match_action = enums.InfoAction.INCLUDE

    def exclude(self) -> None:
        """Use EXCLUDE match operation, AND for filter
        """
        self.filter_use = enums.FilterUse.AND
        self.match_action = enums.InfoAction.EXCLUDE

    def off(self) -> None:
        """Use OFF for filter
        """
        self.filter_use = enums.FilterUse.OFF
        self.match_action = enums.InfoAction.INCLUDE

    def __use_and(self) -> None:
        self.filter_use = enums.FilterUse.AND

    def __use_off(self) -> None:
        self.filter_use = enums.FilterUse.OFF


@dataclass
class ShadowFilterConfigEthernetAddr(ProtocolConfigCommon):
    value: Hex = Hex('000000000000')

    def on(self, value: Hex = Hex('000000000000'), mask: Hex = Hex('FFFFFFFFFFFF')) -> None:
        """Enable th match on this field

        :param value: value of the field, defaults to 000000000000
        :type value: int, optional
        :param mask: value of the mask, defaults to FFFFFFFFFFFF
        :type mask: Hex, optional
        """
        self.use = enums.OnOff.ON
        self.value = value
        self.mask = mask

    def off(self, value: Hex = Hex('000000000000'), mask: Hex = Hex('FFFFFFFFFFFF')) -> None:
        """Disable th match on this field

        :param value: value of the field, defaults to 000000000000
        :type value: int, optional
        :param mask: value of the mask, defaults to FFFFFFFFFFFF
        :type mask: Hex, optional
        """
        self.use = enums.OnOff.OFF
        self.value = value
        self.mask = mask


@dataclass
class FilterProtocolEthernet(FilterConfigCommon):
    src_addr: ShadowFilterConfigEthernetAddr = field(default_factory=ShadowFilterConfigEthernetAddr)
    """Source MAC Address field
    """
    dest_addr: ShadowFilterConfigEthernetAddr = field(default_factory=ShadowFilterConfigEthernetAddr)
    """Destination MAC Address field
    """


@dataclass
class ShadowFilterConfigVLANPCP(ProtocolConfigCommon):
    mask: Hex = Hex('7')
    value: int = 0

    def on(self, value: int = 0, mask: Hex = Hex('7')) -> None:
        """Enable th match on this field

        :param value: value of the field, defaults to 0
        :type value: int, optional
        :param mask: value of the mask, defaults to 7
        :type mask: Hex, optional
        """
        self.use = enums.OnOff.ON
        self.value = value
        self.mask = mask

    def off(self, value: int = 0, mask: Hex = Hex('7')) -> None:
        """Disable th match on this field

        :param value: value of the field, defaults to 0
        :type value: int, optional
        :param mask: value of the mask, defaults to 7
        :type mask: Hex, optional
        """
        self.use = enums.OnOff.OFF
        self.value = value
        self.mask = mask


@dataclass
class FilterProtocolL2VLAN(FilterConfigCommon):
    tag_inner: ProtocolConfigCommon = field(default_factory=ProtocolConfigCommon)
    """Inner VLAN Tag field
    """
    pcp_inner: ShadowFilterConfigVLANPCP = field(default_factory=ShadowFilterConfigVLANPCP)
    """Inner VLAN PCP field
    """
    tag_outer: ProtocolConfigCommon = field(default_factory=ProtocolConfigCommon)
    """Outer VLAN Tag field
    """
    pcp_outer: ShadowFilterConfigVLANPCP = field(default_factory=ShadowFilterConfigVLANPCP)
    """Outer VLAN PCP field
    """


@dataclass
class ShadowFilterConfigMPLSLabel(ProtocolConfigCommon):
    mask: Hex = Hex('FFFFF')
    value: int = 0

    def on(self, value: int = 0, mask: Hex = Hex('FFFFF')) -> None:
        """Enable th match on this field

        :param value: value of the field, defaults to 0
        :type value: int, optional
        :param mask: value of the mask, defaults to FFFFFF
        :type mask: Hex, optional
        """
        self.use = enums.OnOff.ON
        self.value = value
        self.mask = mask

    def off(self, value: int = 0, mask: Hex = Hex('FFFFF')) -> None:
        """Disable th match on this field

        :param value: value of the field, defaults to 0
        :type value: int, optional
        :param mask: value of the mask, defaults to FFFFFF
        :type mask: Hex, optional
        """
        self.use = enums.OnOff.OFF
        self.value = value
        self.mask = mask


@dataclass
class ShadowFilterConfigMPLSTOC(ProtocolConfigCommon):
    mask: Hex = Hex('7')
    value: int = 0

    def on(self, value: int = 0, mask: Hex = Hex('7')) -> None:
        """Enable th match on this field

        :param value: value of the field, defaults to 0
        :type value: int, optional
        :param mask: value of the mask, defaults to 7
        :type mask: Hex, optional
        """
        self.use = enums.OnOff.ON
        self.value = value
        self.mask = mask

    def off(self, value: int = 0, mask: Hex = Hex('7')) -> None:
        """Disable th match on this field

        :param value: value of the field, defaults to 0
        :type value: int, optional
        :param mask: value of the mask, defaults to 7
        :type mask: Hex, optional
        """
        self.use = enums.OnOff.OFF
        self.value = value
        self.mask = mask


@dataclass
class FilterProtocolL2MPLS(FilterConfigCommon):
    label: ShadowFilterConfigMPLSLabel = field(default_factory=ShadowFilterConfigMPLSLabel)
    """MPLS Label field
    """
    toc: ShadowFilterConfigMPLSTOC = field(default_factory=ShadowFilterConfigMPLSTOC)
    """MPLS TOC field
    """


@dataclass
class FilterLayer2Plus:
    present: enums.L2PlusPresent = enums.L2PlusPresent.NA
    vlan: FilterProtocolL2VLAN = field(default_factory=FilterProtocolL2VLAN)
    """VLAN field
    """
    mpls: FilterProtocolL2MPLS = field(default_factory=FilterProtocolL2MPLS)
    """MPLS field
    """

    def use_none(self) -> None:
        """Set protocol field to None
        """
        self.present = enums.L2PlusPresent.NA

    def use_1_vlan_tag(self) -> FilterProtocolL2VLAN:
        """Set protocol field to One VLAN Tag

        :return: One-tag VLAN field object
        :rtype: FilterProtocolL2VLAN
        """
        self.present = enums.L2PlusPresent.VLAN1
        return self.vlan

    def use_2_vlan_tags(self) -> FilterProtocolL2VLAN:
        """Set protocol field to Two VLAN Tags

        :return: Two-tag VLAN field object
        :rtype: FilterProtocolL2VLAN
        """
        self.present = enums.L2PlusPresent.VLAN2
        return self.vlan

    def use_mpls(self) -> FilterProtocolL2MPLS:
        """Set protocol field to MPLS

        :return: MPLS field object
        :rtype: FilterProtocolL2MPLS
        """
        self.present = enums.L2PlusPresent.MPLS
        return self.mpls


@dataclass
class FilterProtocolL3IPv4Addr(ProtocolConfigCommon):
    value: ipaddress.IPv4Address = ipaddress.IPv4Address("0.0.0.0")

    def on(self, value: ipaddress.IPv4Address = ipaddress.IPv4Address('0.0.0.0'), mask: Hex = Hex('FFFFFFFF')) -> None:
        """Enable th match on this field

        :param value: value of the field, defaults to 0.0.0.0
        :type value: int, optional
        :param mask: value of the mask, defaults to FFFFFFFF
        :type mask: Hex, optional
        """
        self.use = enums.OnOff.ON
        self.value = value
        self.mask = mask

    def off(self, value: ipaddress.IPv4Address = ipaddress.IPv4Address('0.0.0.0'), mask: Hex = Hex('FFFFFFFF')) -> None:
        """Disable th match on this field

        :param value: value of the field, defaults to 0.0.0.0
        :type value: int, optional
        :param mask: value of the mask, defaults to FFFFFFFF
        :type mask: Hex, optional
        """
        self.use = enums.OnOff.OFF
        self.value = value
        self.mask = mask


@dataclass
class FilterProtocolL3IPv4DSCP(ProtocolConfigCommon):
    mask: Hex = Hex('FC')
    value: int = 0

    def on(self, value: int = 0, mask: Hex = Hex('FC')) -> None:
        """Enable th match on this field

        :param value: value of the field, defaults to 0
        :type value: int, optional
        :param mask: value of the mask, defaults to FC
        :type mask: Hex, optional
        """
        self.use = enums.OnOff.ON
        self.value = value
        self.mask = mask

    def off(self, value: int = 0, mask: Hex = Hex('FC')) -> None:
        """Disable th match on this field

        :param value: value of the field, defaults to 0
        :type value: int, optional
        :param mask: value of the mask, defaults to FC
        :type mask: Hex, optional
        """
        self.use = enums.OnOff.OFF
        self.value = value
        self.mask = mask


@dataclass
class FilterProtocolL3IPv4(FilterConfigCommon):
    src_addr: FilterProtocolL3IPv4Addr = field(default_factory=FilterProtocolL3IPv4Addr)
    """IPv4 Source Address field
    """
    dest_addr: FilterProtocolL3IPv4Addr = field(default_factory=FilterProtocolL3IPv4Addr)
    """IPv4 Destination Address field
    """
    dscp: FilterProtocolL3IPv4DSCP = field(default_factory=FilterProtocolL3IPv4DSCP)
    """IPv4 DSCP field
    """


@dataclass
class ShadowFilterConfigBasicIPv6SRCADDR(ProtocolConfigCommon):
    value: ipaddress.IPv6Address = ipaddress.IPv6Address('::')
    mask: Hex = Hex('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')

    def on(self, value: ipaddress.IPv6Address = ipaddress.IPv6Address('::'), mask: Hex = Hex('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')) -> None:
        """Enable th match on this field

        :param value: value of the field, defaults to '::'
        :type value: int, optional
        :param mask: value of the mask, defaults to FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        :type mask: Hex, optional
        """
        self.use = enums.OnOff.ON
        self.value = value
        self.mask = mask

    def off(self, value: ipaddress.IPv6Address = ipaddress.IPv6Address('::'), mask: Hex = Hex('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')) -> None:
        """Disable th match on this field

        :param value: value of the field, defaults to '::'
        :type value: int, optional
        :param mask: value of the mask, defaults to FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        :type mask: Hex, optional
        """
        self.use = enums.OnOff.OFF
        self.value = value
        self.mask = mask


@dataclass
class ShadowFilterConfigBasicIPv6DESTADDR(ShadowFilterConfigBasicIPv6SRCADDR):
    pass


@dataclass
class FilterProtocolL3IPv6(FilterConfigCommon):
    src_addr: ShadowFilterConfigBasicIPv6SRCADDR = field(default_factory=ShadowFilterConfigBasicIPv6SRCADDR)
    """IPv6 Source Address Field
    """
    dest_addr: ShadowFilterConfigBasicIPv6DESTADDR = field(default_factory=ShadowFilterConfigBasicIPv6DESTADDR)
    """IPv6 Destination Address Field
    """


@dataclass
class FilterLayer3:
    present: enums.L3PlusPresent = enums.L3PlusPresent.NA
    ipv4: FilterProtocolL3IPv4 = field(default_factory=FilterProtocolL3IPv4)
    ipv6: FilterProtocolL3IPv6 = field(default_factory=FilterProtocolL3IPv6)

    def use_none(self) -> None:
        """Set protocol field to None
        """
        self.present = enums.L3PlusPresent.NA

    def use_ipv4(self) -> FilterProtocolL3IPv4:
        """Set protocol field to IPv4

        :return: IPv4 field object
        :rtype: FilterProtocolL3IPv4
        """
        self.present = enums.L3PlusPresent.IP4
        return self.ipv4

    def use_ipv6(self) -> FilterProtocolL3IPv6:
        """Set protocol field to IPv6

        :return: IPv6 field object
        :rtype: FilterProtocolL3IPv6
        """
        self.present = enums.L3PlusPresent.IP6
        return self.ipv6


@dataclass
class ShadowFilterConfigL4SrcPort(ProtocolConfigCommon):
    mask: Hex = Hex('FFFF')
    value: int = 0

    def on(self, value: int = 0, mask: Hex = Hex('FFFF')) -> None:
        """Enable th match on this field

        :param value: value of the field, defaults to 0
        :type value: int, optional
        :param mask: value of the mask, defaults to FFFF
        :type mask: Hex, optional
        """
        self.use = enums.OnOff.ON
        self.value = value
        self.mask = mask

    def off(self, value: int = 0, mask: Hex = Hex('FFFF')) -> None:
        """Disable th match on this field

        :param value: value of the field, defaults to 0
        :type value: int, optional
        :param mask: value of the mask, defaults to FFFF
        :type mask: Hex, optional
        """
        self.use = enums.OnOff.OFF
        self.value = value
        self.mask = mask


@dataclass
class ShadowFilterConfigL4DestPort(ShadowFilterConfigL4SrcPort):
    pass


@dataclass
class FilterProtocolL4TCP(FilterConfigCommon):
    src_port: ShadowFilterConfigL4SrcPort = field(default_factory=ShadowFilterConfigL4SrcPort)
    """TCP Source Port field
    """
    dest_port: ShadowFilterConfigL4DestPort = field(default_factory=ShadowFilterConfigL4DestPort)
    """TCP Destination Port field
    """


@dataclass
class FilterProtocolL4UDP(FilterProtocolL4TCP):
    pass


@dataclass
class FilterLayer4:
    tcp: FilterProtocolL4TCP = field(default_factory=FilterProtocolL4TCP)
    udp: FilterProtocolL4UDP = field(default_factory=FilterProtocolL4UDP)

    def use_none(self) -> None:
        """Set protocol field to None
        """
        pass

    def use_tcp(self) -> FilterProtocolL4TCP:
        """Set protocol field to TCP

        :return: TCP field object
        :rtype: FilterProtocolL4TCP
        """
        return self.tcp

    def use_udp(self) -> FilterProtocolL4UDP:
        """Set protocol field to UDP

        :return: UDP field object
        :rtype: FilterProtocolL4UDP
        """
        return self.udp


@dataclass
class ShadowFilterConfigTPLDID:
    filter_index: int
    tpld_id: int = 0
    use: enums.OnOff = enums.OnOff.OFF

    def toggle(self, status: enums.OnOff, tpld_id: int = 0) -> None:
        self.use = status
        self.tpld_id = tpld_id

    def on(self, tpld_id: int = 0) -> None:
        """Enable match on this field

        :param tpld_id: Xena's test payload identifier
        :type tpld_id: int
        """
        self.toggle(enums.OnOff.ON, tpld_id)

    def off(self, tpld_id: int = 0) -> None:
        """Disable match on this field

        :param tpld_id: Xena's test payload identifier
        :type tpld_id: int
        """
        self.toggle(enums.OnOff.OFF, tpld_id)


@dataclass
class FilterProtocolTPLD:
    match_action: enums.InfoAction = enums.InfoAction.INCLUDE
    _configs: List[ShadowFilterConfigTPLDID] = field(default_factory=lambda: [ShadowFilterConfigTPLDID(filter_index=i) for i in range(TPLD_FILTERS_LENGTH)])

    def __getitem__(self, tpld_id_index: int) -> ShadowFilterConfigTPLDID:
        assert 0 <= tpld_id_index < TPLD_FILTERS_LENGTH
        return self._configs[tpld_id_index]

    def __setitem__(self, tpld_id_index: int, tpld_id: ShadowFilterConfigTPLDID) -> None:
        self._configs[tpld_id_index] = tpld_id

    def include(self) -> None:
        self.match_action = enums.InfoAction.INCLUDE

    def exclude(self) -> None:
        self.match_action = enums.InfoAction.EXCLUDE

@dataclass
class FilterLayerXena:
    tpld: FilterProtocolTPLD = field(default_factory=FilterProtocolTPLD)

    def use_none(self) -> None:
        """Set protocol field to None
        """
        pass

    def use_tpld(self) -> FilterProtocolTPLD:
        return self.tpld


@dataclass
class FilterProtocolAnyField(FilterConfigCommon):
    position: int = 0
    value: Hex = Hex('000000000000')
    mask: Hex = Hex('FFFFFFFFFFFF')

    def on(self, position: int, value: Hex = Hex('000000000000'), mask: Hex = Hex('FFFFFFFFFFFF')) -> None:
        """Enable match on this field

        :param position: position of the field in the frame
        :type position: int
        :param value: value of the field, defaults to 000000000000
        :type value: Hex, optional
        :param mask: value of the mask, defaults to FFFFFFFFFFFF
        :type mask: Hex, optional
        """
        self.position = position
        self.value = value
        self.mask = mask


@dataclass
class FilterLayerAny(FilterConfigCommon):
    any_field: FilterProtocolAnyField = field(default_factory=FilterProtocolAnyField)

    def use_none(self) -> None:
        """Set protocol field to None
        """
        pass

    def use_any_field(self) -> FilterProtocolAnyField:
        """Set protocol field to Any

        :return: Any field object
        :rtype: FilterProtocolAnyField
        """
        self.any_field.__use_and()
        return self.any_field


@dataclass
class FilterLayer2:
    ethernet: FilterProtocolEthernet = field(default_factory=FilterProtocolEthernet)

    def use_ethernet(self) -> FilterProtocolEthernet:
        """Set protocol field to Ethernet

        :return: subfilter on Ethernet protocol header
        :rtype: FilterProtocolEthernet
        """
        return self.ethernet


@dataclass
class ShadowFilterConfigBasic:
    layer_2: FilterLayer2 = field(default_factory=FilterLayer2)
    """Ethernet (Layer 2) subfilter"""
    layer_2_plus: FilterLayer2Plus = field(default_factory=FilterLayer2Plus)
    """Layer 2+ subfilter"""
    layer_3: FilterLayer3 = field(default_factory=FilterLayer3)
    """Layer 3 subfilter"""
    layer_4: FilterLayer4 = field(default_factory=FilterLayer4)
    """Layer 4 subfilter"""
    layer_xena: FilterLayerXena = field(default_factory=FilterLayerXena)
    """Layer Xena subfilter"""
    layer_any: FilterLayerAny = field(default_factory=FilterLayerAny)
    """Layer any subfilter"""





@dataclass
class ProtocolSegement:
    protocol_type: enums.ProtocolOption
    value: str
    mask: str


@dataclass
class ShadowFilterConfigExtended:
    protocol_segments: Tuple[ProtocolSegement, ...] = field(default_factory=tuple)
    """Protocol segments for the extended shadow filter config"""