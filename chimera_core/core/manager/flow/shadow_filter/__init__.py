from xoa_driver import enums
from xoa_driver.internals.hli_v2.ports.port_l23.chimera.filter_definition.shadow import (
    FilterDefinitionShadow,
    ModeExtendedS,
)
from xoa_driver.internals.hli_v2.ports.port_l23.chimera.filter_definition.general import ModeBasic

from .basic_mode import ShadowFilterBasic
from .extended_mode import ShadowFilterExtended


class ShadowFilterManager:
    def __init__(self, filter: "FilterDefinitionShadow"):
        self.filter = filter

    async def clear(self) -> None:
        """reset shadow filter configuration to its default values.
        """
        await self.filter.initiating.set()

    async def use_basic_mode(self) -> "ShadowFilterBasic":
        mode = await self.filter.get_mode()
        await self.filter.use_basic_mode()
        mode = await self.filter.get_mode()
        assert isinstance(mode, ModeBasic), "Not base mode"
        return ShadowFilterBasic(self.filter, mode)

    async def use_extended_mode(self) -> "ShadowFilterExtended":
        await self.filter.use_extended_mode()
        mode = await self.filter.get_mode()
        assert isinstance(mode, ModeExtendedS), "Not extended mode"
        return ShadowFilterExtended(self.filter, mode)

    async def enable(self) -> None:
        await self.filter.enable.set(enums.OnOff.ON)

    async def disable(self) -> None:
        await self.filter.enable.set(enums.OnOff.OFF)

    async def apply(self) -> None:
        """apply changes made to shadow to working"""
        await self.filter.apply.set()

    async def cancel(self) -> None:
        """cancel changes made to shadow and restore config from working"""
        await self.filter.cancel.set()