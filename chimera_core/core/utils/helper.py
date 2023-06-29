import asyncio
from typing import Union

from xoa_driver import utils
from xoa_driver.v2.testers import L23Tester
from xoa_driver.v2.modules import ModuleChimera
from xoa_driver.v2.ports import PortChimera

from chimera_core.core.manager.const import INTERVEL_CHECK_RESERVE_RESOURCE
from chimera_core.types import enums


TypeResouces = Union[L23Tester, ModuleChimera, PortChimera]


async def reserve_resources(*resources: TypeResouces) -> None:
    async def relinquish(resource: TypeResouces) -> None:
        while enums.ReservedStatus(resource.info.reservation) != enums.ReservedStatus.RELEASED:
            await resource.reservation.set_relinquish()
            await asyncio.sleep(INTERVEL_CHECK_RESERVE_RESOURCE)
    await asyncio.gather(*[relinquish(r) for r in resources if r.info.reservation != enums.ReservedStatus.RESERVED_BY_YOU])

    tokens = []
    for res in resources:
        if res.info.reservation == enums.ReservedStatus.RESERVED_BY_YOU:
            continue

        tokens.append(res.reservation.set_reserve())
        if isinstance(res, PortChimera):
            res.reset.set()

    await utils.apply(*tokens)
