import os
from typing import TYPE_CHECKING, Callable, Dict, Optional, Set, Type, TypeVar, Union

from loguru import logger
from xoa_driver.v2.testers import L23Tester
from xoa_driver.v2.modules import ModuleChimera

from chimera_core.core.manager.tester import TesterManager


from .core.messenger.handler import OutMessagesHandler
from .core.resources.manager import ResourcesManager, AllTesterTypes
from .core import const
from . import exception

if TYPE_CHECKING:
    from .types.resources import EMsgType
    from .core.resources.datasets.external import credentials


T = TypeVar("T", bound="MainController")


class MainController:
    """MainController - A main class of XOA-Core framework."""

    __slots__ = ("__publisher", "__resources", "suites_library", "__testers")

    def __init__(self, *, storage_path: Optional[str] = None, mono: bool = False) -> None:
        __storage_path = os.path.join(os.getcwd(), "store") if not storage_path else storage_path

        self.__publisher = OutMessagesHandler()
        resources_pipe = self.__publisher.get_pipe(const.PIPE_RESOURCES)
        self.__resources = ResourcesManager(resources_pipe, __storage_path)
        self.__testers: Dict[str, L23Tester] = {}

    def listen_changes(self, *names: str, _filter: Optional[Set["EMsgType"]] = None):
        """Subscribe to the messages from different subsystems and test-suites."""
        return self.__publisher.changes(*names, _filter=_filter)

    def __await__(self):
        return self.__setup().__await__()

    async def __setup(self: T) -> T:
        await self.__resources
        return self

    async def list_testers(self) -> Dict[str, "AllTesterTypes"]:
        """List the added testers.

        :return: list of testers
        :rtype: typing.Dict[str, "AllTesterTypes"]
        """
        return await self.__resources.get_all_testers()

    async def add_tester(self, credentials: "credentials.Credentials") -> bool:
        """Add a tester.

        :param credentials: tester login credentials
        :type credentials: credentials.Credentials
        :return: success or failure
        :rtype: bool
        """
        return await self.__resources.add_tester(credentials)

    async def remove_tester(self, tester_id: str) -> None:
        """Remove a tester.

        :param tester_id: tester id
        :type tester_id: str
        """
        await self.__resources.remove_tester(tester_id)

    async def use(self, credentials: "credentials.Credentials", username: str = "chimera_core", reserve: bool = False, debug: bool = False) -> "TesterManager":
        if not (tester_instance := self.__testers.get(username)):
            tester_instance = await self.__resources.get_testers_by_id(
                testers_ids=[credentials.id],
                username=username,
                debug=debug,
            )[credentials.id]

            if not isinstance(tester_instance, L23Tester):
                raise exception.OnlyAcceptL23TesterError()
            if not any(isinstance(module, ModuleChimera) for module in tester_instance.modules):
                raise exception.ChimeraModuleNotExistsError()
            self.__testers[username] = tester_instance

        manager = TesterManager(tester_instance)
        if reserve:
            await manager.reserve_if_not()
        return manager
