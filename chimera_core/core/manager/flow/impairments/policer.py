from xoa_driver import enums

from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import (
    CPolicerImpairment,
)

from .__base import ImpairmentManagerBase
from .__dataset import ImpairmentConfigPolicer


class ImpairmentPolicer(ImpairmentManagerBase[CPolicerImpairment]):
    async def get(self) -> ImpairmentConfigPolicer:
        config = await self.impairment.config.get()

        config = ImpairmentConfigPolicer(
            on_off=config.on_off,
            mode=config.mode,
            cir=config.cir,
            cbs=config.cbs,
        )
        return config