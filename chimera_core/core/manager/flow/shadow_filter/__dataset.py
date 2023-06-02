import ipaddress
from dataclasses import dataclass, field
from typing import Any, Protocol, Tuple, Union

from chimera_core.types import enums


FFF_HEX = 'FFF'
TPLD_FILTERS_LENGTH = 16


class PInnerOuterGetDataAttr(Protocol):
    use: Any
    value: int
    mask: str


@dataclass
class InnerOuter:
    use: enums.OnOff = enums.OnOff.OFF
    mask: str = FFF_HEX
    value: int = 0

    def off(self) -> None:
        self.use = enums.OnOff.OFF

    def on(self, value: int = 0, mask: str = FFF_HEX) -> None:
        self.use = enums.OnOff.ON
        self.value = value
        self.mask = mask


def create_inner_outer(attr: PInnerOuterGetDataAttr) -> InnerOuter:
    return InnerOuter(use=attr.use, value=attr.value, mask=attr.mask.replace('0x', ''))


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
class ShadowFilterConfigEthernetAddr(InnerOuter):
    value: str = '000000000000'

    def on(self, value: str = '000000000000', mask: str = 'FFFFFFFFFFFF') -> None:
        self.use = enums.OnOff.ON
        self.value = value
        self.mask = mask


@dataclass
class ShadowFilterConfigEthernet(FilterConfigCommon):
    src_addr: ShadowFilterConfigEthernetAddr = field(default_factory=ShadowFilterConfigEthernetAddr)
    dest_addr: ShadowFilterConfigEthernetAddr = field(default_factory=ShadowFilterConfigEthernetAddr)


@dataclass
class ShadowFilterConfigL2VLAN(FilterConfigCommon):
    # inner
    tag_inner: InnerOuter = field(default_factory=InnerOuter)
    pcp_inner: InnerOuter = field(default_factory=InnerOuter)
    # outer
    tag_outer: InnerOuter = field(default_factory=InnerOuter)
    pcp_outer: InnerOuter = field(default_factory=InnerOuter)


@dataclass
class ShadowFilterConfigL2MPLS(FilterConfigCommon):
    label: InnerOuter = field(default_factory=InnerOuter)
    toc: InnerOuter = field(default_factory=InnerOuter)


@dataclass
class ShadowFilterLayer2Plus:
    present: enums.L2PlusPresent = enums.L2PlusPresent.NA
    vlan: ShadowFilterConfigL2VLAN = field(default_factory=ShadowFilterConfigL2VLAN)
    mpls: ShadowFilterConfigL2MPLS = field(default_factory=ShadowFilterConfigL2MPLS)

    def use_none(self) -> None:
        self.present = enums.L2PlusPresent.NA

    def use_1_vlan_tag(self) -> ShadowFilterConfigL2VLAN:
        self.present = enums.L2PlusPresent.VLAN1
        return self.vlan

    def use_2_vlan_tags(self) -> ShadowFilterConfigL2VLAN:
        self.present = enums.L2PlusPresent.VLAN2
        return self.vlan

    def use_mpls(self) -> ShadowFilterConfigL2MPLS:
        self.present = enums.L2PlusPresent.MPLS
        return self.mpls


@dataclass
class ShadowFilterConfigL2IPv4Addr(InnerOuter):
    value: ipaddress.IPv4Address = ipaddress.IPv4Address("0.0.0.0")

    def on(self, address: ipaddress.IPv4Address = ipaddress.IPv4Address('0.0.0.0'), mask: str = 'FFFFFFFF') -> None:
        self.use = enums.OnOff.ON
        self.value = address
        self.mask = mask


@dataclass
class ShadowFilterConfigL2IPv4DSCP(InnerOuter):
    pass


@dataclass
class ShadowFilterConfigL3IPv4(FilterConfigCommon):
    src_addr: ShadowFilterConfigL2IPv4Addr = field(default_factory=ShadowFilterConfigL2IPv4Addr)
    dest_addr: ShadowFilterConfigL2IPv4Addr = field(default_factory=ShadowFilterConfigL2IPv4Addr)
    dscp: ShadowFilterConfigL2IPv4DSCP = field(default_factory=ShadowFilterConfigL2IPv4DSCP)


@dataclass
class ShadowFilterConfigBasicIPv6SRCADDR(InnerOuter):
    value: str = '::'
    mask: str = 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'

    def on(self, value: str = '00000000000000000000000000000000', mask: str = 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF') -> None:
        self.use = enums.OnOff.ON
        self.value = value
        self.mask = mask


@dataclass
class ShadowFilterConfigBasicIPv6DESTADDR(ShadowFilterConfigBasicIPv6SRCADDR):
    pass


@dataclass
class ShadowFilterConfigL3IPv6(FilterConfigCommon):
    src_addr: ShadowFilterConfigBasicIPv6SRCADDR = field(default_factory=ShadowFilterConfigBasicIPv6SRCADDR)
    dest_addr: ShadowFilterConfigBasicIPv6DESTADDR = field(default_factory=ShadowFilterConfigBasicIPv6DESTADDR)


@dataclass
class ShadowFilterLayer3:
    present: enums.L3PlusPresent = enums.L3PlusPresent.NA
    ipv4: ShadowFilterConfigL3IPv4 = field(default_factory=ShadowFilterConfigL3IPv4)
    ipv6: ShadowFilterConfigL3IPv6 = field(default_factory=ShadowFilterConfigL3IPv6)

    def use_none(self) -> None:
        self.present = enums.L3PlusPresent.NA

    def use_ipv4(self) -> ShadowFilterConfigL3IPv4:
        self.present = enums.L3PlusPresent.IP4
        return self.ipv4

    def use_ipv6(self) -> ShadowFilterConfigL3IPv6:
        self.present = enums.L3PlusPresent.IP6
        return self.ipv6


@dataclass
class ShadowFilterConfigL4UDPSRCPort(InnerOuter):
    pass


@dataclass
class ShadowFilterConfigL4UDPDESTPort(InnerOuter):
    pass


@dataclass
class ShadowFilterConfigL4TCP(FilterConfigCommon):
    src_port: InnerOuter = field(default_factory=InnerOuter)
    dest_port: InnerOuter = field(default_factory=InnerOuter)


@dataclass
class ShadowFilterConfigL4UDP(ShadowFilterConfigL4TCP):
    pass


@dataclass
class ShadowFilterLayer4:
    tcp: ShadowFilterConfigL4TCP = field(default_factory=ShadowFilterConfigL4TCP)
    udp: ShadowFilterConfigL4UDP = field(default_factory=ShadowFilterConfigL4UDP)

    def use_none(self) -> None:
        pass

    def use_tcp(self) -> ShadowFilterConfigL4TCP:
        return self.tcp

    def use_udp(self) -> ShadowFilterConfigL4UDP:
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
class ShadowFilterConfigTPLD(FilterConfigCommon):
    configs: Tuple[ShadowFilterConfigTPLDID, ...] = tuple(ShadowFilterConfigTPLDID(filter_index=i) for i in range(16))


@dataclass
class ShadowFilterLayerXena:
    tpld: ShadowFilterConfigTPLD = field(default_factory=ShadowFilterConfigTPLD)

    def use_tpld(self) -> ShadowFilterConfigTPLD:
        self.tpld.__use_and()
        return self.tpld


@dataclass
class ShadowFilterConfigAnyField(FilterConfigCommon):
    position: int = 0
    value: str = '000000000000'
    mask: str = 'FFFFFFFFFFFF'

    def on(self, position: int, value: str = '000000000000', mask: str = 'FFFFFFFFFFFF') -> None:
        self.position = position
        self.value = value
        self.mask = mask


@dataclass
class ShadowFilterLayerAny(FilterConfigCommon):
    any_field: ShadowFilterConfigAnyField = field(default_factory=ShadowFilterConfigAnyField)

    def use_any_field(self) -> ShadowFilterConfigAnyField:
        self.any_field.__use_and()
        return self.any_field


@dataclass
class ShadowFilterLayer2:
    ethernet: ShadowFilterConfigEthernet = field(default_factory=ShadowFilterConfigEthernet)

    def use_ethernet(self) -> ShadowFilterConfigEthernet:
        return self.ethernet


@dataclass
class ShadowFilterConfigBasic:
    layer_2: ShadowFilterLayer2 = field(default_factory=ShadowFilterLayer2)
    layer_2_plus: ShadowFilterLayer2Plus = field(default_factory=ShadowFilterLayer2Plus)
    layer_3: ShadowFilterLayer3 = field(default_factory=ShadowFilterLayer3)
    layer_4: ShadowFilterLayer4 = field(default_factory=ShadowFilterLayer4)
    layer_xena: ShadowFilterLayerXena = field(default_factory=ShadowFilterLayerXena)
    layer_any: ShadowFilterLayerAny = field(default_factory=ShadowFilterLayerAny)





@dataclass
class ProtocolSegement:
    protocol_type: enums.ProtocolOption
    value: str
    mask: str


@dataclass
class ShadowFilterConfigExtended:
    protocol_segments: Tuple[ProtocolSegement, ...] = field(default_factory=tuple)