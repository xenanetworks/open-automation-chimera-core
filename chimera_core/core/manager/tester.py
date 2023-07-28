from typing import  Generator

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
        """Select and use a module by its index.

        :param module_id: module index
        :type module_id: int
        :param reserve: should reserve the module or not, defaults to False
        :type reserve: bool, optional
        :return: module manager object
        :rtype: ModuleManager
        """
        manager = ModuleManager(self._obtain_module(module_id))
        if reserve:
            await manager.reserve()
        return manager

    async def use_port(self, module_id: int, port_id: int, reserve: bool = True) -> "PortManager":
        """Select and use a port by its index.

        :param module_id: module index
        :type module_id: int
        :param port_id: port index
        :type port_id: int
        :param reserve: should reserve the port or not, defaults to True
        :type reserve: bool, optional
        :raises InvalidChimeraResourceError: the port is not a Chimera port
        :return: port manager object
        :rtype: PortManager
        """
        module = self._obtain_module(module_id)
        port = module.ports.obtain(port_id)
        if not isinstance(port, PortChimera):
            raise InvalidChimeraResourceError('port')
        manager = PortManager(port)
        if reserve:
            await manager.reserve()
        return manager
