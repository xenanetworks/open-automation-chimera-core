import asyncio
from xoa_driver.v2.testers import L23Tester
from xoa_driver.v2.modules import ModuleChimera

from chimera_core.core.utils.helper import TypeResouces, reserve_resources


class ReserveMixin:
    resource_instance: TypeResouces

    async def reserve_if_not(self) -> None:
        coroutines = []
        if isinstance(self.resource_instance, L23Tester):
            coroutines.extend(
                reserve_resources(module) for module in self.resource_instance.modules if isinstance(module, ModuleChimera)
            )
        elif isinstance(self.resource_instance, ModuleChimera):
            coroutines.extend(reserve_resources(port) for port in self.resource_instance.ports)

        asyncio.gather(*coroutines)
        await reserve_resources(self.resource_instance)
