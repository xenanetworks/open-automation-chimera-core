import os
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Set, Type, TypeVar, Union

from loguru import logger
from xoa_driver.v2.testers import L23Tester
from xoa_driver.v2.modules import ModuleChimera

from chimera_core.core.manager.tester import TesterManager


from .core.messenger.handler import OutMessagesHandler
from .core.resources.controller import ResourcesController
from .core.resources.storage import PrecisionStorage
from .core.resources.types import Credentials, TesterInfoModel, TesterID
from .core import const
from . import exception

if TYPE_CHECKING:
    from .types.dataset import EMsgType


T = TypeVar("T", bound="MainController")


class MainController:
    """MainController - A main class of XOA Chimera Core framework."""

    __slots__ = ("__publisher", "__resources", "suites_library", "__testers", "__is_started")

    def __init__(self, *, storage_path: Optional[str] = None) -> None:
        self.__is_started = False
        __storage_path = os.path.join(os.getcwd(), "store") if not storage_path else storage_path
        self.__publisher = OutMessagesHandler()
        resources_pipe = self.__publisher.get_pipe(const.PIPE_RESOURCES)
        storage = PrecisionStorage(str(__storage_path))
        self.__resources = ResourcesController(resources_pipe, storage)
        self.__testers: Dict[str, L23Tester] = {}

    def listen_changes(self, *names: str, _filter: Optional[Set["EMsgType"]] = None):
        """Subscribe to the messages from different subsystems and test-suites."""
        return self.__publisher.changes(*names, _filter=_filter)

    def __await__(self):
        return self.__setup().__await__()

    async def __setup(self: T) -> T:
        if not self.__is_started:
            await self.__resources.start()
            self.__is_started = True
        return self

    async def list_testers(self) -> List[TesterInfoModel]:
        """List the added testers.

        :return: list of testers
        :rtype: typing.Dict[str, "AllTesterTypes"]
        """
        return await self.__resources.list_testers_info()

    async def add_tester(self, credentials: "Credentials") -> TesterID:
        """Add a tester.

        :param credentials: tester login credentials
        :type credentials: credentials.Credentials
        :return: success or failure
        :rtype: bool
        """
        return await self.__resources.add_tester(credentials)

    async def remove_tester(self, tester_id: TesterID) -> None:
        """Remove a tester.

        :param tester_id: tester id
        :type tester_id: str
        """
        await self.__resources.remove_tester(tester_id)

    async def use_tester(self, tester_id: TesterID, username: str = "chimera-core", reserve: bool = False, debug: bool = False) -> "TesterManager":
        """Select and use a tester by its ID.

        :param tester_id: tester identifier
        :type tester_id: TesterID
        :param username: username, defaults to "chimera_core"
        :type username: str, optional
        :param reserve: should reserve the tester or not, defaults to False
        :type reserve: bool, optional
        :param debug: should enable debug mode or not, defaults to False
        :type debug: bool, optional
        :raises exception.OnlyAcceptL23TesterError: the tester type is not supported
        :raises exception.ChimeraModuleNotExistsError: the tester doesn't have a Chimera module
        :return: tester object
        :rtype: TesterManager
        """
        if not (tester_instance := self.__testers.get(username)):
            tester_instance = await self.__resources.get_testers_by_id(
                testers_ids=[tester_id],
                username=username,
                debug=debug,
            )[tester_id]

            if not isinstance(tester_instance, L23Tester):
                raise exception.OnlyAcceptL23TesterError()
            if not any(isinstance(module, ModuleChimera) for module in tester_instance.modules):
                raise exception.ChimeraModuleNotExistsError()
            self.__testers[username] = tester_instance

        manager = TesterManager(tester_instance)
        if reserve:
            await manager.reserve()
        return manager
