import asyncio

from xoa_driver  import utils
from xoa_driver.internals.hli_v2.ports.port_l23.chimera.filter_definition.shadow import (
    FilterDefinitionShadow,
    ModeExtendedS,
)
from xoa_driver.internals.hli_v2.ports.port_l23.chimera.filter_definition.general import ProtocolSegment as HLIProtocolSegment

from .__dataset import (
    ProtocolSegement,
    ShadowFilterConfigExtended,
)


class ShadowFilterConfiguratorExtended:
    def __init__(self, filter_: "FilterDefinitionShadow", extended_mode: "ModeExtendedS") -> None:
        self.shadow_filter = filter_
        self.extended_mode = extended_mode

    async def get_single_protocol_segment_content(self, protocol_segment: HLIProtocolSegment) -> ProtocolSegement:
        value, mask = await utils.apply(
            protocol_segment.value.get(),
            protocol_segment.mask.get(),
        )
        value = ''.join(h.replace('0x', '') for h in value.value)
        mask = ''.join(h.replace('0x', '') for h in mask.masks)
        return ProtocolSegement(
            protocol_type=protocol_segment.segment_type,
            value=value,
            mask=mask,
        )

    async def set_single_protocol_segment_content(self, protocol_segment: HLIProtocolSegment, value: str, mask: str) -> None:
        await utils.apply(
            protocol_segment.value.set(value),
            protocol_segment.mask.set(mask),
        )

    async def get(self) -> ShadowFilterConfigExtended:
        protocol_types = await self.extended_mode.get_protocol_segments()
        segments = await asyncio.gather(*(
            self.get_single_protocol_segment_content(protocol_segment=proto) for proto in protocol_types
        ))
        return ShadowFilterConfigExtended(protocol_segments=tuple(segments))

    async def set(self, config: ShadowFilterConfigExtended) -> None:
        await self.extended_mode.use_segments(*(proto.protocol_type for proto in config.protocol_segments[1:]))
        protocol_types = await self.extended_mode.get_protocol_segments()
        await asyncio.gather(*(
            self.set_single_protocol_segment_content(
                protocol_segment=proto,
                value=config.protocol_segments[idx].value,
                mask=config.protocol_segments[idx].mask,
            )
                for idx, proto in enumerate(protocol_types)
        ))