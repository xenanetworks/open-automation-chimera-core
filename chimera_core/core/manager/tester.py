from typing import TYPE_CHECKING, Generator
from chimera_core.core.manager.base import ReserveMixin

from loguru import logger
from xoa_driver.v2.modules import ModuleChimera
from xoa_driver.v2.ports import PortChimera
from xoa_driver.v2.testers import L23Tester

from .module import ModuleManager
from .port import PortManager


class TesterManager(ReserveMixin):
    def __init__(self, tester: L23Tester, reserve: bool = False) -> None:
        self.resource_instance: L23Tester = tester
        self._reserve = reserve

    async def setup(self) -> "TesterManager":
        if self._reserve:
            await self.reserve_if_not()
        return self

    def __await__(self) -> Generator[None, None, "TesterManager"]:
        return self.setup().__await__()

    def _obtain_module(self, module_id: int) -> ModuleChimera:
        module = self.resource_instance.modules.obtain(module_id)
        if not isinstance(module, ModuleChimera):
            raise ValueError('Chimera Module Only')
        return module

    def use_module(self, module_id: int, reserve: bool = False) -> "ModuleManager":
        return ModuleManager(self._obtain_module(module_id), reserve=reserve)

    def use_port(self, module_id: int, port_id: int, reserve: bool = False) -> PortManager:
        module = self._obtain_module(module_id)
        port = module.ports.obtain(port_id)
        if not isinstance(port, PortChimera):
            raise ValueError('Chimera Port Only')
        return PortManager(port, reserve=reserve)
