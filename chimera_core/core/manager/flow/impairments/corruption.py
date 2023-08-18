from xoa_driver.v2.misc import (
    CCorruptionImpairment,
)

from .__base import ImpairmentManagerGeneral, DistributionResponseValidator
from .__dataset import BatchReadDistributionConfigFromServer, ImpairmentConfigCorruption


class ImpairmentCorruption(ImpairmentManagerGeneral[CCorruptionImpairment]):
    def configure_distributions(self) -> None:
        self.read_distribution_config_from_server = BatchReadDistributionConfigFromServer(
            fixed_burst=True,
            random_burst=True,
            fixed_rate=True,
            random_rate=True,
            bit_error_rate=True,
            ge=True,
            uniform=True,
            gaussian=True,
            gamma=True,
            poisson=True,
            custom=True,
        )
        self.allow_set_distribution_class_name = self.load_allow_set_class_name('corruption')

    async def get(self) -> ImpairmentConfigCorruption:
        return await super().get(ImpairmentConfigCorruption)
