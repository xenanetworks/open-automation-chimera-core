import asyncio
from typing import Union

from loguru import logger
from xoa_driver import enums, utils
from xoa_driver.v2.testers import L23Tester
from xoa_driver.v2.modules import ModuleChimera
from xoa_driver.v2.ports import PortChimera

from chimera_core.core.manager.const import INTERVEL_CHECK_RESERVE_RESOURCE


TypeResouces = Union[L23Tester, ModuleChimera, PortChimera]


async def reserve_resources(*resources: TypeResouces) -> None:
    async def relinquish(resource: TypeResouces) -> None:
        logger.debug(resource)
        while enums.ReservedStatus(resource.info.reservation) != enums.ReservedStatus.RELEASED:
            await resource.reservation.set_relinquish()
            await asyncio.sleep(INTERVEL_CHECK_RESERVE_RESOURCE)
    await asyncio.gather(*[relinquish(r) for r in resources if r.info.reservation != enums.ReservedStatus.RESERVED_BY_YOU])

    tokens = []
    for res in resources:
        if res.info.reservation == enums.ReservedStatus.RESERVED_BY_YOU:
            continue

        tokens.append(res.reservation.set_reserve())
        logger.debug(res.info.reserved_by)
        if isinstance(res, PortChimera):
            res.reset.set()

    await utils.apply(*tokens)
