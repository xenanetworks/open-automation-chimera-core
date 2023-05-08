from xoa_driver import enums

from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import (
    CShaperImpairment,
)

from .base import ImpairmentConfiguratorBase
from ..dataset import ImpairmentConfigPolicer


class ImpairmentShaper(ImpairmentConfiguratorBase[CShaperImpairment]):
    async def get(self) -> ImpairmentConfigPolicer:
        config = await self.impairment.config.get()

        config = ImpairmentConfigPolicer(
            on_off=enums.OnOff(config.on_off),
            mode=enums.PolicerMode(config.mode),
            cir=config.cir,
            cbs=config.cbs,
        )
        return config