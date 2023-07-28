import asyncio
import importlib
from typing import Any, Dict, Generic, Optional, Tuple, Type, TypeVar, Union

from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import (
    CDropImpairment,
    CMisorderingImpairment,
    CLatencyJitterImpairment,
    CDuplicationImpairment,
    CCorruptionImpairment,
)
from xoa_driver.v2.misc import Token

from .__dataset import (
    TImpairmentGeneral,
    BatchReadDistributionConfigFromServer,
    ImpairmentConfigGeneral,
    ImpairmentConfigBase,
    DistributionResponseValidator,
    ImpairmentConfigCorruption,
)


class ImpairmentManagerBase(Generic[TImpairmentGeneral]):
    def __init__(self, impairment: TImpairmentGeneral):
        self.impairment = impairment
        self.config: Optional[ImpairmentConfigBase] = None

    async def start(self, config: Optional[Any] = None) -> None:
        """Start the impairment

        :param config: the impairment configuration, defaults to None
        :type config: Optional[Any], optional
        """
        await self.toggle(True, config)

    async def stop(self, config: Optional[Any] = None) -> None:
        """Stop the impairment

        :param config: the impairment configuration, defaults to None
        :type config: Optional[Any], optional
        """
        await self.toggle(False, config)

    async def toggle(self, state: bool, config: Optional[ImpairmentConfigBase] = None) -> None:
        """Toggle the impairment

        :param state: state of the impairment
        :type state: bool
        :param config: the impairment configuration, defaults to None
        :type config: Optional[ImpairmentConfigBase], optional
        """
        config = config or self.config
        assert config, "Config not exists"
        await asyncio.gather(*config._start(self.impairment) if state else config._stop(self.impairment))

    async def set(self, config: ImpairmentConfigBase) -> None:
        """Set the impairment

        :param config: the impairment configuration
        :type config: ImpairmentConfigBase
        """
        self.config = config
        await asyncio.gather(*config._apply(self.impairment))


TImpairmentWithDistribution = TypeVar(
    'TImpairmentWithDistribution',
    CLatencyJitterImpairment,
    CDropImpairment,
    CMisorderingImpairment,
    CLatencyJitterImpairment,
    CDuplicationImpairment,
    CCorruptionImpairment,
)

TConfig = Union[ImpairmentConfigGeneral, ImpairmentConfigCorruption]

class ImpairmentManagerGeneral(ImpairmentManagerBase[TImpairmentWithDistribution]):
    read_distribution_config_from_server: BatchReadDistributionConfigFromServer
    allow_set_distribution_class_name: Tuple[str, ...]

    def __init__(self, impairment: TImpairmentWithDistribution) -> None:
        super().__init__(impairment)
        self.configure_distributions()

    def configure_distributions(self) -> None:
        pass

    def load_allow_set_class_name(self, impairment_name: str) -> Tuple[str, ...]:
        return importlib.import_module(name=f'chimera_core.core.manager.flow.distributions.{impairment_name}').__all__

    def batch_read_distribution_config_commands(self) -> Dict[str, Token]:
        result = {}
        for distribution in self.read_distribution_config_from_server.enabled_distributions:
            result[distribution.name] = getattr(self.impairment.distribution, distribution.name).get()

        result['enable'] = self.impairment.enable.get()
        result['schedule'] = self.impairment.schedule.get()
        return result

    async def get(self, impairment_config_class: Optional[Type[TConfig]] = None) -> TConfig:
        command_tokens = self.batch_read_distribution_config_commands()
        command_response = await asyncio.gather(*command_tokens.values(), return_exceptions=True)
        response_mapping = dict(zip(command_tokens.keys(), command_response))

        impairment_config_class = impairment_config_class or ImpairmentConfigGeneral # type: ignore
        assert impairment_config_class

        config = impairment_config_class(
            read_distribution_config_from_server=self.read_distribution_config_from_server,
            allow_set_distribution_class_name=self.allow_set_distribution_class_name,
        )
        config.load_value_from_server_response(DistributionResponseValidator(**response_mapping))
        return config