from xoa_driver import enums

from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import (
    CShaperImpairment,
)

from .__base import ImpairmentManagerBase
from .__dataset import ImpairmentConfigShaper


class ImpairmentShaper(ImpairmentManagerBase[CShaperImpairment]):
    async def get(self) -> ImpairmentConfigShaper:
        config = await self.impairment.config.get()

        config = ImpairmentConfigShaper(
            on_off=config.on_off,
            mode=config.mode,
            cir=config.cir,
            cbs=config.cbs,
            buffer_size=config.buffer_size,
        )
        return config