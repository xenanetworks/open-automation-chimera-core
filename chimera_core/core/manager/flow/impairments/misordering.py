from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import (
    CMisorderingImpairment,
)


from .__base import ImpairmentManagerGeneral
from .__dataset import BatchReadDistributionConfigFromServer, ImpairmentConfigMisordering


class ImpairmentMisordering(ImpairmentManagerGeneral[CMisorderingImpairment]):
    def configure_distributions(self) -> None:
        self.read_distribution_config_from_server = BatchReadDistributionConfigFromServer(
            fixed_burst=True,
            fixed_rate=True,
        )
        self.allow_set_distribution_class_name = self.load_allow_set_class_name('misordering')


    async def get(self) -> ImpairmentConfigMisordering:
        config = await super().get(ImpairmentConfigMisordering)
        assert isinstance(config, ImpairmentConfigMisordering)
        config.depth = (await self.impairment.depth.get()).depth
        return config