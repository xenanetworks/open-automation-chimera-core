
from xoa_driver.v2.misc import (
    CDropImpairment,

)

from .__base import ImpairmentManagerGeneral
from .__dataset import BatchReadDistributionConfigFromServer


class ImpairmentDrop(ImpairmentManagerGeneral[CDropImpairment]):
    def configure_distributions(self) -> None:
        self.read_distribution_config_from_server = BatchReadDistributionConfigFromServer(
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
        self.allow_set_distribution_class_name = self.load_allow_set_class_name('drop')