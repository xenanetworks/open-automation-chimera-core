from typing import  Generator

from loguru import logger
from xoa_driver.v2.modules import ModuleChimera
from xoa_driver.v2.ports import PortChimera
from xoa_driver.v2.testers import L23Tester

from chimera_core.core.manager.__base import ReserveMixin
from .module import ModuleManager
from .port import PortManager
from .exception import InvalidChimeraResourceError


class TesterManager(ReserveMixin):
    def __init__(self, tester: L23Tester) -> None:
        self.resource_instance: L23Tester = tester

    async def setup(self) -> "TesterManager":
        return self

    def __await__(self) -> Generator[None, None, "TesterManager"]:
        return self.setup().__await__()

    def _obtain_module(self, module_id: int) -> "ModuleChimera":
        module = self.resource_instance.modules.obtain(module_id)
        if not isinstance(module, ModuleChimera):
            raise InvalidChimeraResourceError('module')
        return module

    async def use_module(self, module_id: int, reserve: bool = False) -> "ModuleManager":
        manager = ModuleManager(self._obtain_module(module_id))
        if reserve:
            await manager.reserve_if_not()
        return manager

    async def use_port(self, module_id: int, port_id: int, reserve: bool = False) -> "PortManager":
        module = self._obtain_module(module_id)
        port = module.ports.obtain(port_id)
        if not isinstance(port, PortChimera):
            raise InvalidChimeraResourceError('port')
        manager = PortManager(port)
        if reserve:
            await manager.reserve_if_not()
        return manager
