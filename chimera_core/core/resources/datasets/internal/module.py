import asyncio
from typing import (
    Tuple,
    Optional,
    Callable,
    TypeVar,
    Type,
    Dict,
    Any,
)
from dataclasses import dataclass
from xoa_driver import enums
from xoa_driver.v2 import modules

from chimera_core.core.utils import decorators
from .port import PortModel



M = TypeVar("M", bound="ModuleModel")
@dataclass
class ModuleModel:
    id: int
    model: str
    reserved_by: str
    ports: Tuple[PortModel, ...]
    name: str = " - "
    can_media_config: bool = False # used by UI validation (Test Module Config - Media Configuration) & config validation
    is_chimera: bool = False
    can_local_time_adjust: bool = False # used by UI validation (Test Module Config - Local Clock Adjustment) & config validation
    max_clock_ppm: Optional[int] = None # used by UI validation (Test Module Config - Local Clock Adjustment) & config validation


    async def on_evt_reserved_by(self, response) -> None:
        self.reserved_by = response.values.username

    @classmethod
    async def from_module(cls: Type[M], module: "modules.GenericAnyModule", notifier: Callable) -> M:
        inst = cls(
            id = module.module_id,
            model = module.info.model,
            reserved_by = module.info.reserved_by,
            **await _prepare_values(module),
            ports = tuple(
                await asyncio.gather(*[
                    PortModel.from_port(port, notifier)
                    for port in module.ports
                ])
            )
        )
        module.on_reserved_by_change(decorators.post_notify(notifier)(inst.on_evt_reserved_by))
        return inst


async def _prepare_values(module: "modules.GenericAnyModule") -> Dict[str, Any]:
    m_cpb = dict()
    if not isinstance(module, (modules.ModuleL47, modules.ModuleL47VE)):
        cpb = await module.capabilities.get()
        m_cpb["can_media_config"] = cpb.can_media_config is enums.YesNo.YES
        m_cpb["is_chimera"] = cpb.is_chimera is enums.YesNo.YES
        m_cpb["can_local_time_adjust"] = cpb.can_local_time_adjust is enums.YesNo.YES
        m_cpb["max_clock_ppm"] = cpb.max_clock_ppm

    if m_name := getattr(module, "name", None):
        mn = await m_name.get()
        m_cpb["name"] = mn.name
    return m_cpb