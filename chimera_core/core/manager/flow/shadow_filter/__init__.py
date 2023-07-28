from typing import Union
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
        """
        Reset shadow filter configuration to its default values.
        """
        await self.filter.initiating.set()

    async def use_basic_mode(self) -> "ShadowFilterBasic":
        """In Basic mode, the flow filters are composed of multiple sub-filters, which match against different protocol layers. 
        Sub-filters are named after the protocol layer at which they are applied.

        :return: a basic shadow filter object
        :rtype: ShadowFilterBasic
        """
        mode = await self.filter.get_mode()
        await self.filter.use_basic_mode()
        mode = await self.filter.get_mode()
        assert isinstance(mode, ModeBasic), "Not basic mode"
        return ShadowFilterBasic(self.filter, mode)

    async def use_extended_mode(self) -> "ShadowFilterExtended":
        """Extended filtering mode allows the user to filter on any pattern within the first 128 bytes of the packet.
        The filtering is done by specifying a “filter value” of 128 bytes and “filter mask” of 128 bytes.

        :return: an extended shadow filter object
        :rtype: ShadowFilterExtended
        """
        await self.filter.use_extended_mode()
        mode = await self.filter.get_mode()
        assert isinstance(mode, ModeExtendedS), "Not extended mode"
        return ShadowFilterExtended(self.filter, mode)

    async def get_mode(self) -> Union["ShadowFilterBasic", "ShadowFilterExtended"]:
        hli_mode = await self.filter.get_mode()
        mode = {
            ModeBasic: ShadowFilterBasic,
            ModeExtendedS: ShadowFilterExtended,
        }[type(hli_mode)]
        return mode(self.filter, hli_mode)

    async def enable(self) -> None:
        """
        Enables the filter
        """
        await self.filter.enable.set(enums.OnOff.ON)

    async def disable(self) -> None:
        """
        Disable the filter
        """
        await self.filter.enable.set(enums.OnOff.OFF)

    async def apply(self) -> None:
        """Transfer all the shadow filter register values to the working registers instantaneously for all flow filter settings, 
        including all sub-filters in basic mode, so flow filters are always coherent. 
        This allows updating the shadow registers, without the risk of using intermediate filtering values."""
        await self.filter.apply.set()

    async def cancel(self) -> None:
        """Cancel changes made to the shadow filter and restore the configuration from the working filter."""
        await self.filter.cancel.set()

    async def init(self) -> None:
        """Initialize the filter"""
        await self.filter.initiating.set()