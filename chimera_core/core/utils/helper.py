import asyncio
from typing import Union
from xoa_driver import enums, utils
from xoa_driver.v2 import modules, ports

from loguru import logger


async def reserve_modules_ports(*resources: Union[ports.GenericAnyPort, modules.ModuleChimera]) -> None:
    async def relinquish(port: Union[ports.GenericAnyPort, modules.ModuleChimera]):
        logger.debug(enums.ReservedStatus(port.info.reservation) is enums.ReservedStatus.RESERVED_BY_OTHER)
        if enums.ReservedStatus(port.info.reservation) == enums.ReservedStatus.RESERVED_BY_OTHER:
            await port.reservation.set_relinquish()
            while enums.ReservedStatus(port.info.reservation) != enums.ReservedStatus.RELEASED:
                await asyncio.sleep(0.01)
    await asyncio.gather(*[ relinquish(port) for port in resources ])

    tokens = []
    for res in resources:
        if res.info.reservation == enums.ReservedStatus.RESERVED_BY_YOU:
            continue

        tokens.append(res.reservation.set_reserve())
        logger.debug(res)
        if isinstance(res, ports.BasePortL23):
            res.reset.set()

    await utils.apply(*tokens)