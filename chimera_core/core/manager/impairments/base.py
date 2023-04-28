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

from .dataset import SupportedDistribution


class ImpairmentConfiguratorBase(Generic[T]):
    supported_distribution = SupportedDistribution

    def __init__(self, impairment: T):
        self.impairment = impairment
        self.config: Optional[Any] = None
        self.post_init()

    def post_init(self) -> None:
        pass

    def get_all_distribution_commands(self) -> Dict[str, Token]:
        result = {}
        for distribution in self.supported_distribution:
            if (is_supported := getattr(self.supported_distribution, distribution.name)):
                result[distribution.name] = getattr(self.impairment.distribution, distribution.name).get()
        return result


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

    async def _get_enable_and_schedule(self) -> Tuple[commands.PED_ENABLE.GetDataAttr, commands.PED_SCHEDULE.GetDataAttr]:
        assert not isinstance(self.impairment, (CPolicerImpairment, CShaperImpairment))
        enable, schedule = await asyncio.gather(*(
            self.impairment.enable.get(),
            self.impairment.schedule.get(),
        ))
        return enable, schedule

    async def set(self, config: "ImpairmentWithDistribution") -> None:
        await asyncio.gather(*config.apply(self.impairment))