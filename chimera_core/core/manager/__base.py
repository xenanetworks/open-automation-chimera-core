import asyncio
from xoa_driver.v2.testers import L23Tester
from xoa_driver.v2.modules import ModuleChimera

from chimera_core.core.utils.helper import TypeResouces, reserve_resources


class ReserveMixin:
    resource_instance: TypeResouces

    async def reserve(self) -> None:
        """Reserve the resource if it is not reserved already.
        """
        coroutines = []
        if isinstance(self.resource_instance, L23Tester):
            coroutines.extend(
                reserve_resources(module) for module in self.resource_instance.modules if isinstance(module, ModuleChimera)
            )
        elif isinstance(self.resource_instance, ModuleChimera):
            coroutines.extend(reserve_resources(port) for port in self.resource_instance.ports)

        asyncio.gather(*coroutines)
        await reserve_resources(self.resource_instance)

    async def free(self, should_free_sub_resources: bool) -> None:
        """Free the resource. 

        :param should_free_sub_resources: specifies if its sub resources are also to be freed.
        :type should_free_sub_resources: bool
        """
