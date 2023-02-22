import asyncio
from typing import (
    TYPE_CHECKING,
    Optional,
    Tuple,
    Callable,
    TypeVar,
    Type,
)
from pydantic import (
    SecretStr,
    constr,
)
from dataclasses import dataclass, field
if TYPE_CHECKING:
    from xoa_driver.v2 import testers
from xoa_driver import utils
from chimera_core.core.utils import decorators
from chimera_core.core.resources.datasets import enums
from .module import ModuleModel

T = TypeVar("T", bound="TesterModel")

@dataclass
class TesterModel:
    product: enums.EProductType
    host: str
    port: int
    password: SecretStr
    name: str = " - "
    reserved_by: str = ""
    is_connected: bool = False
    modules: Tuple[ModuleModel, ...] = field(default_factory=tuple)
    id: Optional[constr(regex=r'^[a-fA-F\d]{32}$')] = None # type: ignore
    keep_disconnected: bool = False
    max_name_len: int = 0 # used by UI validation (Tester Name) & config validation
    max_comment_len: int = 0 # used by UI validation (Tester Description) & config validation
    max_password_len: int = 0 # used by UI validation (Tester Password) & config validation

    async def on_evt_reserved_by(self, response) -> None:
        self.reserved_by = response.values.username

    async def on_evt_disconnected(self, *_) -> None:
        self.is_connected = False
        self.modules = tuple()

    @classmethod
    async def from_tester(cls: Type[T], resource_id: str, product: "enums.EProductType", tester: "testers.GenericAnyTester", notifier: Callable) -> T:
        tn, cpb = await utils.apply(
            tester.name.get(),
            tester.capabilities.get()
        )
        inst = cls(
            id=resource_id,
            product=product,
            host=tester.info.host,
            port=tester.info.port,
            password=SecretStr(tester.session.pwd),
            name=str(tn.chassis_name),
            reserved_by=tester.info.reserved_by,
            is_connected=tester.session.is_online,
            keep_disconnected=False,
            max_name_len=cpb.max_name_len,
            max_comment_len=cpb.max_name_len,
            max_password_len=cpb.max_name_len,
            modules = tuple(
                await asyncio.gather(*[
                    ModuleModel.from_module(module, notifier)
                    for module in tester.modules
                ])
            )
        )
        tester.on_reserved_by_change(decorators.post_notify(notifier)(inst.on_evt_reserved_by))
        tester.on_disconnected(decorators.post_notify(notifier)(inst.on_evt_disconnected))
        return inst