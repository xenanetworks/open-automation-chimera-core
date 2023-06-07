import asyncio
from typing import TYPE_CHECKING, Generator

from chimera_core.core.manager.__base import ReserveMixin
from .__dataset import ModuleConfig

if TYPE_CHECKING:
    from xoa_driver.v2.modules import ModuleChimera


class ModuleConfigurator:
    def __init__(self, module: "ModuleChimera") -> None:
        self.module = module

    async def get(self) -> ModuleConfig:
        comment, clock_ppb, tx_clock_source, tx_clock_status, latency_mode, \
            cfp_type, cfp_config, bypass_mode = await asyncio.gather(*(
                self.module.comment.get(),
                self.module.clock_ppb.get(),
                self.module.tx_clock.source.get(),
                self.module.tx_clock.status.get(),
                self.module.latency_mode.get(),
                self.module.cfp.type.get(),
                self.module.cfp.config.get(),
                self.module.bypass_mode.get(),
            ))

        return ModuleConfig(
            comment=comment.comment,
            clock_ppb=clock_ppb.ppb,
            tx_clock_source=tx_clock_source.tx_clock,
            tx_clock_status=tx_clock_status.status,
            latency_mode=latency_mode.mode,
            cfp_type=cfp_type.type,
            cfp_state=cfp_type.state,
            port_speed=cfp_config.portspeed_list,
            bypass_mode=bypass_mode.on_off,
        )

    async def set(self, config: ModuleConfig) -> None:
        coroutines = (
            self.module.comment.set(config.comment),
            self.module.clock_ppb.set(config.clock_ppb),
            self.module.tx_clock.source.set(config.tx_clock_source),
            self.module.latency_mode.set(config.latency_mode),
            self.module.cfp.config.set(config.port_speed),
            self.module.bypass_mode.set(config.bypass_mode),
        )
        await asyncio.gather(*coroutines)


class ModuleManager(ReserveMixin):
    def __init__(self, module: "ModuleChimera") -> None:
        self.resource_instance = module
        self.config = ModuleConfigurator(module)

    async def setup(self) -> "ModuleManager":
        return self

    def __await__(self) -> Generator[None, None, "ModuleManager"]:
        return self.setup().__await__()
