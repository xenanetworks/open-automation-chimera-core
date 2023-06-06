import ipaddress
from dataclasses import dataclass, field
from typing import Any,  Protocol, Tuple

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
    mask: Hex = Hex(FFF_HEX)
    value: int = 0

    def off(self, value: int = 0, mask: Hex = Hex('0FFF')) -> None:
        self.use = enums.OnOff.OFF
        self.value = value
        self.mask = mask

    def on(self, value: int = 0, mask: Hex = Hex(FFF_HEX)) -> None:
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
        return self.filter_use == enums.FilterUse.OFF

    def include(self) -> None:
        self.filter_use = enums.FilterUse.AND
        self.match_action = enums.InfoAction.INCLUDE

    def exclude(self) -> None:
        self.filter_use = enums.FilterUse.AND
        self.match_action = enums.InfoAction.EXCLUDE

    def __use_and(self) -> None:
        self.filter_use = enums.FilterUse.AND

    def __use_off(self) -> None:
        self.filter_use = enums.FilterUse.OFF


@dataclass
class ShadowFilterConfigEthernetAddr(ProtocolConfigCommon):
    value: Hex = Hex('000000000000')

    def on(self, value: Hex = Hex('000000000000'), mask: Hex = Hex('FFFFFFFFFFFF')) -> None:
        self.use = enums.OnOff.ON
        self.value = value
        self.mask = mask


@dataclass
class FilterProtocolEthernet(FilterConfigCommon):
    src_addr: ShadowFilterConfigEthernetAddr = field(default_factory=ShadowFilterConfigEthernetAddr)
    dest_addr: ShadowFilterConfigEthernetAddr = field(default_factory=ShadowFilterConfigEthernetAddr)


@dataclass
class FilterProtocolL2VLAN(FilterConfigCommon):
    # inner
    tag_inner: ProtocolConfigCommon = field(default_factory=ProtocolConfigCommon)
    pcp_inner: ProtocolConfigCommon = field(default_factory=ProtocolConfigCommon)
    # outer
    tag_outer: ProtocolConfigCommon = field(default_factory=ProtocolConfigCommon)
    pcp_outer: ProtocolConfigCommon = field(default_factory=ProtocolConfigCommon)


@dataclass
class FilterProtocolL2MPLS(FilterConfigCommon):
    label: ProtocolConfigCommon = field(default_factory=ProtocolConfigCommon)
    toc: ProtocolConfigCommon = field(default_factory=ProtocolConfigCommon)


@dataclass
class FilterLayer2Plus:
    present: enums.L2PlusPresent = enums.L2PlusPresent.NA
    vlan: FilterProtocolL2VLAN = field(default_factory=FilterProtocolL2VLAN)
    mpls: FilterProtocolL2MPLS = field(default_factory=FilterProtocolL2MPLS)

    def use_none(self) -> None:
        self.present = enums.L2PlusPresent.NA

    def use_1_vlan_tag(self) -> FilterProtocolL2VLAN:
        self.present = enums.L2PlusPresent.VLAN1
        return self.vlan

    def use_2_vlan_tags(self) -> FilterProtocolL2VLAN:
        self.present = enums.L2PlusPresent.VLAN2
        return self.vlan

    def use_mpls(self) -> FilterProtocolL2MPLS:
        self.present = enums.L2PlusPresent.MPLS
        return self.mpls


@dataclass
class FilterProtocolL3IPv4Addr(ProtocolConfigCommon):
    value: ipaddress.IPv4Address = ipaddress.IPv4Address("0.0.0.0")

    def on(self, address: ipaddress.IPv4Address = ipaddress.IPv4Address('0.0.0.0'), mask: Hex = Hex('FFFFFFFF')) -> None:
        self.use = enums.OnOff.ON
        self.value = address
        self.mask = mask


@dataclass
class FilterProtocolL3IPv4DSCP(ProtocolConfigCommon):
    pass


@dataclass
class FilterProtocolL3IPv4(FilterConfigCommon):
    src_addr: FilterProtocolL3IPv4Addr = field(default_factory=FilterProtocolL3IPv4Addr)
    dest_addr: FilterProtocolL3IPv4Addr = field(default_factory=FilterProtocolL3IPv4Addr)
    dscp: FilterProtocolL3IPv4DSCP = field(default_factory=FilterProtocolL3IPv4DSCP)


@dataclass
class ShadowFilterConfigBasicIPv6SRCADDR(ProtocolConfigCommon):
    value: ipaddress.IPv6Address = ipaddress.IPv6Address('::')
    mask: Hex = Hex('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')

    def on(self, value: ipaddress.IPv6Address = ipaddress.IPv6Address('::'), mask: Hex = Hex('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')) -> None:
        self.use = enums.OnOff.ON
        self.value = value
        self.mask = mask


@dataclass
class ShadowFilterConfigBasicIPv6DESTADDR(ShadowFilterConfigBasicIPv6SRCADDR):
    pass


@dataclass
class FilterProtocolL3IPv6(FilterConfigCommon):
    src_addr: ShadowFilterConfigBasicIPv6SRCADDR = field(default_factory=ShadowFilterConfigBasicIPv6SRCADDR)
    dest_addr: ShadowFilterConfigBasicIPv6DESTADDR = field(default_factory=ShadowFilterConfigBasicIPv6DESTADDR)


@dataclass
class FilterLayer3:
    present: enums.L3PlusPresent = enums.L3PlusPresent.NA
    ipv4: FilterProtocolL3IPv4 = field(default_factory=FilterProtocolL3IPv4)
    ipv6: FilterProtocolL3IPv6 = field(default_factory=FilterProtocolL3IPv6)

    def use_none(self) -> None:
        self.present = enums.L3PlusPresent.NA

    def use_ipv4(self) -> FilterProtocolL3IPv4:
        self.present = enums.L3PlusPresent.IP4
        return self.ipv4

    def use_ipv6(self) -> FilterProtocolL3IPv6:
        self.present = enums.L3PlusPresent.IP6
        return self.ipv6


@dataclass
class ShadowFilterConfigL4UDPSRCPort(ProtocolConfigCommon):
    pass


@dataclass
class ShadowFilterConfigL4UDPDESTPort(ProtocolConfigCommon):
    pass


@dataclass
class FilterProtocolL4TCP(FilterConfigCommon):
    src_port: ProtocolConfigCommon = field(default_factory=ProtocolConfigCommon)
    dest_port: ProtocolConfigCommon = field(default_factory=ProtocolConfigCommon)


@dataclass
class FilterProtocolL4UDP(FilterProtocolL4TCP):
    pass


@dataclass
class FilterLayer4:
    tcp: FilterProtocolL4TCP = field(default_factory=FilterProtocolL4TCP)
    udp: FilterProtocolL4UDP = field(default_factory=FilterProtocolL4UDP)

    def use_none(self) -> None:
        pass

    def use_tcp(self) -> FilterProtocolL4TCP:
        return self.tcp

    def use_udp(self) -> FilterProtocolL4UDP:
        return self.udp


@dataclass
class ShadowFilterConfigTPLDID:
    filter_index: int
    tpld_id: int = 0
    use: enums.OnOff = enums.OnOff.OFF

    def on(self, tpld_id: int) -> None:
        self.use = enums.OnOff.ON
        self.tpld_id = tpld_id


@dataclass
class FilterProtocolTPLD(FilterConfigCommon):
    configs: Tuple[ShadowFilterConfigTPLDID, ...] = tuple(ShadowFilterConfigTPLDID(filter_index=i) for i in range(16))


@dataclass
class FilterLayerXena:
    tpld: FilterProtocolTPLD = field(default_factory=FilterProtocolTPLD)

    def use_tpld(self) -> FilterProtocolTPLD:
        self.tpld.__use_and()
        return self.tpld


@dataclass
class FilterProtocolAnyField(FilterConfigCommon):
    position: int = 0
    value: Hex = Hex('000000000000')
    mask: Hex = Hex('FFFFFFFFFFFF')

    def on(self, position: int, value: Hex = Hex('000000000000'), mask: Hex = Hex('FFFFFFFFFFFF')) -> None:
        self.position = position
        self.value = value
        self.mask = mask


@dataclass
class FilterLayerAny(FilterConfigCommon):
    any_field: FilterProtocolAnyField = field(default_factory=FilterProtocolAnyField)

    def use_any_field(self) -> FilterProtocolAnyField:
        self.any_field.__use_and()
        return self.any_field


@dataclass
class FilterLayer2:
    ethernet: FilterProtocolEthernet = field(default_factory=FilterProtocolEthernet)

    def use_ethernet(self) -> FilterProtocolEthernet:
        return self.ethernet


@dataclass
class ShadowFilterConfigBasic:
    layer_2: FilterLayer2 = field(default_factory=FilterLayer2)
    layer_2_plus: FilterLayer2Plus = field(default_factory=FilterLayer2Plus)
    layer_3: FilterLayer3 = field(default_factory=FilterLayer3)
    layer_4: FilterLayer4 = field(default_factory=FilterLayer4)
    layer_xena: FilterLayerXena = field(default_factory=FilterLayerXena)
    layer_any: FilterLayerAny = field(default_factory=FilterLayerAny)





@dataclass
class ProtocolSegement:
    protocol_type: enums.ProtocolOption
    value: str
    mask: str


@dataclass
class ShadowFilterConfigExtended:
    protocol_segments: Tuple[ProtocolSegement, ...] = field(default_factory=tuple)