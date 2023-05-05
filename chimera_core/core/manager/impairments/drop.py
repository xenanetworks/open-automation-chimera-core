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
from chimera_core.core.manager.distributions.drop import __all__ as DD


class ImpairmentDrop(ImpairmentConfiguratorBase[CDropImpairment]):
    def init_supported_distribution(self) -> None:
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
        self.supported_distribution_class = DD

    async def get(self) -> ImpairmentWithDistribution:
        command_tokens = self.get_all_distribution_commands()
        results = await asyncio.gather(*command_tokens.values(), return_exceptions=True)
        distributions = dict(zip(command_tokens.keys(), results))
        config = ImpairmentWithDistribution(
            supported_distribution=self.supported_distribution,
            supported_distribution_class=DD,
        )
        config.load_value_from_server_response(DistributionResponseValidator(**distributions))
        return config