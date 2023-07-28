from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import (
    CDuplicationImpairment,
)


from .__base import ImpairmentManagerGeneral
from .__dataset import BatchReadDistributionConfigFromServer


class ImpairmentDuplication(ImpairmentManagerGeneral[CDuplicationImpairment]):
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
        self.allow_set_distribution_class_name = self.load_allow_set_class_name('duplication')