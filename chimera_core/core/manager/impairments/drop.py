import asyncio

from loguru import logger

from xoa_driver import enums
from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import (
    CDropImpairment,
    CMisorderingImpairment,
    CLatencyJitterImpairment,
    CPolicerImpairment,
    CDuplicationImpairment,
    CCorruptionImpairment,
    CShaperImpairment,
)


from .base import ImpairmentConfiguratorBase
from .dataset import ImpairmentWithDistribution, DistributionResponseValidator, SupportedDistribution


class ImpairmentDrop(ImpairmentConfiguratorBase[CDropImpairment]):
    def post_init(self) -> None:
        self.supported_distribution = SupportedDistribution(
            fixed_burst=True,
            random_burst=True,
            fixed_rate=True,
            bit_error_rate=True,
            ge=True,
            uniform=True,
            gaussian=True,
            gamma=True,
            poisson=True,
            custom=True,
        )

    async def get(self) -> ImpairmentWithDistribution:
        all_tokens = self.get_all_distribution_commands()
        results = await asyncio.gather(*all_tokens.values(), return_exceptions=True)
        distributions = dict(zip(all_tokens.keys(), results))
        enable, schedule = await self._get_enable_and_schedule()
        config = ImpairmentWithDistribution(enable=enums.OnOff(enable.action))
        config.distribution.load_value_from_server_response(DistributionResponseValidator(**distributions))
        config.distribution.set_schedule(schedule)
        return config