from typing import TYPE_CHECKING

from xoa_driver.v2.modules import ModuleChimera
from loguru import logger

from chimera_core.core.session.module import ModuleHandlerManager, ModuleHandler

if TYPE_CHECKING:
    from xoa_driver.testers import GenericAnyTester



class Session:
    def __init__(self, tester: "GenericAnyTester") -> None:
        self.tester = tester
        self.modules = ModuleHandlerManager([ModuleHandler(m) for m in self.tester.modules if isinstance(m, ModuleChimera)])


