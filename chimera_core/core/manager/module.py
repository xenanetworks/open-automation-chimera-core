import asyncio
from typing import TYPE_CHECKING, Generator, List, Optional
from chimera_core.core.manager.base import ReserveMixin

from xoa_driver import enums
from loguru import logger

from chimera_core.core.utils.helper import reserve_resources
from .dataset import ModuleConfig

if TYPE_CHECKING:
    from xoa_driver.v2.modules import ModuleChimera


class ModuleConfigurator:
    def __init__(self, module: "ModuleChimera") -> None:
        self.module = module

    async def get(self) -> ModuleConfig:
        comment, tx_clock_source, tx_clock_status = await asyncio.gather(*(
            self.module.comment.get(),
            self.module.tx_clock.source.get(),
            self.module.tx_clock.status.get(),
        ))
        return ModuleConfig(
            comment=comment.comment,
            tx_clock_source=enums.TXClockSource(tx_clock_source.tx_clock),
            tx_clock_status=enums.TXClockStatus(tx_clock_status.status),
        )

    async def set(self, config: ModuleConfig) -> None:
        await self.module.comment.set(config.comment)


class ModuleManager(ReserveMixin):
    def __init__(self, module: "ModuleChimera") -> None:
        self.resource_instance = module
        self.config = ModuleConfigurator(module)

    async def setup(self) -> "ModuleManager":
        return self

    def __await__(self) -> Generator[None, None, "ModuleManager"]:
        return self.setup().__await__()
