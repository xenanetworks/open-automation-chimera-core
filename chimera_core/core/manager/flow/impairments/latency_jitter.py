
from xoa_driver.v2.misc import (
    CLatencyJitterImpairment,
)


from .__base import ImpairmentManagerGeneral
from .__dataset import BatchReadDistributionConfigFromServer


class ImpairmentLatencyJitter(ImpairmentManagerGeneral[CLatencyJitterImpairment]):
    def configure_distributions(self) -> None:
        self.read_distribution_config_from_server = BatchReadDistributionConfigFromServer(
            constant_delay=True,
            accumulate_and_burst=True,
            step=True,
            uniform=True,
            gaussian=True,
            gamma=True,
            poisson=True,
            custom=True,
        )
        self.allow_set_distribution_class_name = self.load_allow_set_class_name('latency_jitter')