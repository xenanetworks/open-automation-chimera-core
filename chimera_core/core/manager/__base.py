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

    async def free(self) -> None:
        """Free the resource.
        If the resource is reserved by you, release the resource.
        If the resource is reserved by others, relinquish the resource.
        """
