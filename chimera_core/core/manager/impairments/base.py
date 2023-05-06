import asyncio
from dataclasses import fields
from typing import Any, Dict, Generic, Optional, Tuple, TypeVar

from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import (
    CDropImpairment,
    CMisorderingImpairment,
    CLatencyJitterImpairment,
    CPolicerImpairment,
    CDuplicationImpairment,
    CCorruptionImpairment,
    CShaperImpairment,
)
from xoa_driver.v2.misc import Token
from xoa_driver.lli import commands

T = TypeVar(
    'T',
    CLatencyJitterImpairment,
    CDropImpairment,
    CMisorderingImpairment,
    CLatencyJitterImpairment,
    CPolicerImpairment,
    CDuplicationImpairment,
    CCorruptionImpairment,
    CShaperImpairment,
)

from .dataset import ReadDistributionsFromServer, ImpairmentWithDistribution, DistributionResponseValidator

from loguru import logger


class ImpairmentConfiguratorBase(Generic[T]):
    def __init__(self, impairment: T):
        self.impairment = impairment
        self.config: Optional[Any] = None



    async def start(self, config: Optional[Any] = None) -> None:
        await self.toggle(True, config)
        # if isinstance(self, (CPolicerImpairment, CShaperImpairment)):
        #     await self.config.set()
        # await self.impairment.enable.set(enums.OnOff(state))

    async def stop(self, config: Optional[Any] = None) -> None:
        await self.toggle(False, config)

    async def toggle(self, state: bool, config: Optional[Any] = None) -> None:
        config = config or self.config
        assert config, "Config not exists"
        await asyncio.gather(*config.start(self.impairment) if state else config.stop())

    async def set(self, config: "ImpairmentWithDistribution") -> None:
        await asyncio.gather(*config.apply(self.impairment))



TImpairmentWithDistribution = TypeVar(
    'TImpairmentWithDistribution',
    CLatencyJitterImpairment,
    CDropImpairment,
    CMisorderingImpairment,
    CLatencyJitterImpairment,
    CDuplicationImpairment,
)

class ImpairmentWithDistributionConfigurator(ImpairmentConfiguratorBase[TImpairmentWithDistribution]):
    read_distributions_from_server: ReadDistributionsFromServer
    allow_set_distribution_class_name: Tuple[str, ...]

    def __init__(self, impairment: TImpairmentWithDistribution) -> None:
        super().__init__(impairment)
        self.setup_supported_distribution()

    def setup_supported_distribution(self) -> None:
        pass

    def get_all_distribution_commands(self) -> Dict[str, Token]:
        result = {}
        for distribution in self.read_distributions_from_server:
            logger.debug(distribution)
            if (is_supported := getattr(self.read_distributions_from_server, distribution.name)):
                result[distribution.name] = getattr(self.impairment.distribution, distribution.name).get()

        result['enable'] = self.impairment.enable.get()
        result['enable'] = self.impairment.schedule.get()
        return result

    async def get(self) -> ImpairmentWithDistribution:
        command_tokens = self.get_all_distribution_commands()
        results = await asyncio.gather(*command_tokens.values(), return_exceptions=True)
        distributions = dict(zip(command_tokens.keys(), results))
        config = ImpairmentWithDistribution(
            read_distributions_from_server=self.read_distributions_from_server,
            allow_set_distribution_class_name=self.allow_set_distribution_class_name,
        )
        config.load_value_from_server_response(DistributionResponseValidator(**distributions))
        return config