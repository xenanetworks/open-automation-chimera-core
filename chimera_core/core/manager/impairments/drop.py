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


from .base import ImpairmentWithDistributionConfigurator
from .dataset import ReadDistributionsFromServer
from chimera_core.core.manager.distributions.drop import __all__ as allow_set_distribution_class_name


class ImpairmentDrop(ImpairmentWithDistributionConfigurator[CDropImpairment]):
    def setup_supported_distribution(self) -> None:
        self.read_distributions_from_server = ReadDistributionsFromServer(
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
        self.allow_set_distribution_class_name = allow_set_distribution_class_name