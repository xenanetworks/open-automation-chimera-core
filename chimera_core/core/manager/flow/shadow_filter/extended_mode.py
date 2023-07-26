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
    Hex,
)


class ShadowFilterExtended:
    def __init__(self, shadow_filter_hli: "FilterDefinitionShadow", extended_mode_hli: "ModeExtendedS") -> None:
        self.shadow_filter = shadow_filter_hli
        self.extended_mode = extended_mode_hli

    async def get_single_protocol_segment_content(self, hli_protocol_segment: HLIProtocolSegment) -> ProtocolSegement:
        value, mask = await utils.apply(
            hli_protocol_segment.value.get(),
            hli_protocol_segment.mask.get(),
        )
        value = ''.join(h.replace('0x', '') for h in value.value)
        mask = ''.join(h.replace('0x', '') for h in mask.masks)
        return ProtocolSegement(
            protocol_type=hli_protocol_segment.segment_type,
            value=value,
            mask=mask,
        )

    async def set_single_protocol_segment_content(self, protocol_segment_hli: HLIProtocolSegment, value: str, mask: str) -> None:
        await utils.apply(
            protocol_segment_hli.value.set(Hex(value)),
            protocol_segment_hli.mask.set(Hex(mask)),
        )

    async def get(self) -> ShadowFilterConfigExtended:
        """Get the configuration of the shadow filter that is in extended mode

        :return: the configuration of the shadow filter that is in extended mode
        :rtype: ShadowFilterConfigExtended
        """
        protocol_types = await self.extended_mode.get_protocol_segments()
        segments = await asyncio.gather(*(
            self.get_single_protocol_segment_content(hli_protocol_segment=proto) for proto in protocol_types
        ))
        return ShadowFilterConfigExtended(protocol_segments=tuple(segments))

    async def set(self, config: ShadowFilterConfigExtended) -> None:
        """Set the configuration of the shadow filter that is in extended mode

        :param config: the configuration of the shadow filter that is in extended mode
        :type config: ShadowFilterConfigExtended
        """
        await self.extended_mode.use_segments(*(proto.protocol_type for proto in config.protocol_segments[1:]))
        protocol_types = await self.extended_mode.get_protocol_segments()
        await asyncio.gather(*(
            self.set_single_protocol_segment_content(
                protocol_segment_hli=proto,
                value=config.protocol_segments[idx].value,
                mask=config.protocol_segments[idx].mask,
            )
                for idx, proto in enumerate(protocol_types)
        ))