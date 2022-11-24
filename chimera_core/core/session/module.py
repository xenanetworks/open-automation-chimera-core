import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generator, List, Optional

from xoa_driver import enums
from loguru import logger

from chimera_core.core.session.port import PortHandler, PortHandlerManager
from chimera_core.core.utils.helper import reserve_modules_ports
from chimera_core.core.session.dataset import ModuleConfig

if TYPE_CHECKING:
    from xoa_driver.v2.modules import ModuleChimera


class ModuleConfigurationHandler:
    def __init__(self, module: "ModuleChimera") -> None:
        self.module = module

    async def get(self) -> ModuleConfig:
        comment, tx_clock_source, tx_clock_status = await asyncio.gather(*
            (
                self.module.comment.get(),
                self.module.tx_clock.source.get(),
                self.module.tx_clock.status.get(),
            )
        )
        return ModuleConfig(
            comment=comment.comment,
            tx_clock_source=enums.TXClockSource(tx_clock_source.tx_clock),
            tx_clock_status=enums.TXClockStatus(tx_clock_status.status),
        )

    async def set(self, config: Optional[ModuleConfig] = None, comment: Optional[str] = '') -> None:
        if not config:
            config = ModuleConfig(
                comment=comment,
            )
        await reserve_modules_ports(self.module)

        if config.comment:
            await self.module.comment.set(config.comment)




class ModuleHandler:
    def __init__(self, module: "ModuleChimera") -> None:
        self.module_instance = module
        self.config = ModuleConfigurationHandler(module)
        self.ports = PortHandlerManager([PortHandler(p) for p in self.module_instance.ports])

    async def setup(self) -> "ModuleHandler":
        logger.debug('called')
        await reserve_modules_ports(self.module_instance)
        return self

    def __await__(self) -> Generator[None, None, "ModuleHandler"]:
        return self.setup().__await__()

@dataclass
class ModuleHandlerManager:
    modules: List[ModuleHandler]

    def __getitem__(self, index: int) -> ModuleHandler:
        module = self.modules[index]
        return module
