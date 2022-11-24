import asyncio
from typing import Union
from xoa_driver import enums, utils
from xoa_driver.v2 import modules, ports

from loguru import logger


async def reserve_modules_ports(*resources: Union[ports.GenericAnyPort, modules.ModuleChimera]) -> None:
    async def relinquish(resource: Union[ports.GenericAnyPort, modules.ModuleChimera]):
        logger.debug(resource)
        while enums.ReservedStatus(resource.info.reservation) != enums.ReservedStatus.RELEASED:
            await resource.reservation.set_relinquish()
            await asyncio.sleep(0.01)
    await asyncio.gather(*[ relinquish(r) for r in resources if  r.info.reservation != enums.ReservedStatus.RESERVED_BY_YOU])

    tokens = []
    for res in resources:
        if res.info.reservation == enums.ReservedStatus.RESERVED_BY_YOU:
            continue

        tokens.append(res.reservation.set_reserve())
        logger.debug(res.info.reserved_by)
        if isinstance(res, ports.BasePortL23):
            res.reset.set()

    await utils.apply(*tokens)