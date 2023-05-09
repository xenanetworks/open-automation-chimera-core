from xoa_driver import enums
from xoa_driver.internals.hli_v2.ports.port_l23.chimera.filter_definition.shadow import (
    FilterDefinitionShadow,
    ModeExtendedS,
)

from xoa_driver.internals.hli_v2.ports.port_l23.chimera.filter_definition.general import ModeBasic

from .basic_mode import (
    ShadowFilterConfiguratorBasic,
)
from .extended_mode import ShadowFilterConfiguratorExtended


class ShadowFilterManager:
    def __init__(self, filter: "FilterDefinitionShadow"):
        self.filter = filter

    async def reset(self) -> None:
        await self.filter.initiating.set()

    async def use_basic_mode(self) -> "ShadowFilterConfiguratorBasic":
        await self.filter.use_basic_mode()
        mode = await self.filter.get_mode()
        assert isinstance(mode, ModeBasic), "Not base mode"
        return ShadowFilterConfiguratorBasic(self.filter, mode)

    async def use_extended_mode(self) -> "ShadowFilterConfiguratorExtended":
        await self.filter.use_extended_mode()
        mode = await self.filter.get_mode()
        assert isinstance(mode, ModeExtendedS), "Not extended mode"
        return ShadowFilterConfiguratorExtended(self.filter, mode)

    async def enable(self, state: bool) -> None:
        await self.filter.enable.set(enums.OnOff(state))
        if state:
            await self.filter.apply.set()