import asyncio
from typing import Union

from xoa_driver.enums import ReservedStatus
from xoa_driver.v2.testers import L23Tester
from xoa_driver.v2.modules import ModuleChimera
from xoa_driver.v2.ports import PortChimera

from chimera_core.core.manager.const import INTERVEL_CHECK_RESERVE_RESOURCE


TypeResouces = Union[L23Tester, ModuleChimera, PortChimera]


class ReserveMixin:
    resource_instance: TypeResouces

    async def __reserve_resource(self, resource: TypeResouces) -> None:
        await resource.reservation.set_reserve()

    async def __reserve_port(self, port: PortChimera):
        await self.__free_port(port)
        await self.__reserve_resource(port)

    async def __reserve_module(self, module: ModuleChimera):
        await self.__free_module(module, should_free_sub_resources=True)
        await self.__reserve_resource(module)

    async def __reserve_tester(self, tester: L23Tester):
        await self.__free_tester(tester, should_free_sub_resources=True)
        await self.__reserve_resource(tester)

    async def reserve(self) -> None:
        """Reserve the resource if it is not reserved already.
        """
        if isinstance(self.resource_instance, L23Tester):
            await self.__reserve_tester(self.resource_instance)
        elif isinstance(self.resource_instance, ModuleChimera):
            await self.__reserve_module(self.resource_instance)
        elif isinstance(self.resource_instance, PortChimera):
            await self.__reserve_port(self.resource_instance)

    async def __relinquish(self, resource: TypeResouces) -> None:
        if self.__is_reserved_by_others(resource):
            while ReservedStatus(resource.info.reservation) != ReservedStatus.RELEASED:
                await resource.reservation.set_relinquish()
                await asyncio.sleep(INTERVEL_CHECK_RESERVE_RESOURCE)

    async def __release(self, resource: TypeResouces) -> None:
        if resource.info.reservation != ReservedStatus.RELEASED:
            await resource.reservation.set_release()

    def __is_reserved_by_others(self, resource: TypeResouces) -> bool:
        return resource.info.reservation == ReservedStatus.RESERVED_BY_OTHER

    def __is_reserved_by_you(self, resource: TypeResouces) -> bool:
        return resource.info.reservation == ReservedStatus.RESERVED_BY_YOU

    async def __free_port(self, port: PortChimera) -> None:
        if self.__is_reserved_by_you(port):
            return None

        await self.__relinquish(port)
        await self.__release(port)

    async def __free_module(self, module: ModuleChimera, should_free_sub_resources: bool = False) -> None:
        if self.__is_reserved_by_you(module):
            return None

        await self.__relinquish(module)
        await self.__release(module)

        if should_free_sub_resources:
            await asyncio.gather((self.__free_port(p) for p in module.ports))

    async def __free_tester(self, tester: L23Tester, should_free_sub_resources: bool = False) -> None:
        if self.__is_reserved_by_you(tester):
            return None

        await self.__relinquish(tester)
        await self.__release(tester)

        if should_free_sub_resources:
            await asyncio.gather((
                self.__free_module(m, should_free_sub_resources=True) for m in tester.modules if isinstance(m, ModuleChimera)
            ))

    async def free(self, should_free_sub_resources: bool) -> None:
        """Free the resource.

        :param should_free_sub_resources: specifies if its sub resources are also to be freed.
        :type should_free_sub_resources: bool
        """
        if isinstance(self.resource_instance, L23Tester):
            await self.__free_tester(self.resource_instance, should_free_sub_resources)
        elif isinstance(self.resource_instance, ModuleChimera):
            await self.__free_module(self.resource_instance, should_free_sub_resources)
        elif isinstance(self.resource_instance, PortChimera):
            await self.__free_port(self.resource_instance)
