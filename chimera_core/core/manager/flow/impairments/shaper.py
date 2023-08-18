from xoa_driver.v2.misc import (
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