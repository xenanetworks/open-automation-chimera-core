from dataclasses import dataclass
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from xoa_driver.modules import ModuleChimera


class ModuleConfigurationHandler:
    def __init__(self, module: "ModuleChimera") -> None:
        self.module = module

    async def get(self):
        self.module.comment.get()
        self.module.tx_clock.get()


class ModuleHandler:
    def __init__(self, module: "ModuleChimera") -> None:
        self.module_instance = module
        self.config = ModuleConfigurationHandler(module)


@dataclass
class ModuleHandlerManager:
    modules: List[ModuleHandler]

    def __getitem__(self, index: int) -> ModuleHandler:
        return self.modules[index]
