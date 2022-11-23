from typing import TYPE_CHECKING

from loguru import logger
from xoa_driver import utils

from chimera_core.core.session.dataset import LatencyJitterConfigDistribution, LatencyJitterConfigMain, LatencyJitterConfigSchedule

if TYPE_CHECKING:
    from xoa_driver.internals.hli_v2.ports.port_l23.chimera.port_emulation import CLatencyJitterImpairment


class LatencyJitterHandler:
    def __init__(self, impairment: "CLatencyJitterImpairment"):
        self.impairment = impairment


    async def get(self) -> LatencyJitterConfigMain:
        constant_delay, schedule = await utils.apply(
            self.impairment.distribution.constant_delay.get(),
            self.impairment.schedule.get()
        )
        logger.debug(constant_delay)

        return LatencyJitterConfigMain(
            distribution=LatencyJitterConfigDistribution(constant_delay=constant_delay.delay),
            schedule=LatencyJitterConfigSchedule(duration=schedule.duration, period=schedule.period)
        )