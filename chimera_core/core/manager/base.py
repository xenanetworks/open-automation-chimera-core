from chimera_core.core.utils.helper import TypeResouces, reserve_resources


class ReserveMixin:
    resource_instance: TypeResouces

    async def reserve_if_not(self) -> None:
        await reserve_resources(self.resource_instance)
