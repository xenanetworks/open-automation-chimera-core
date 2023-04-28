class OnlyAcceptL23TesterError(ValueError):
    def __init__(self) -> None:
        self.msg = "Only accept L23 tester."
        super().__init__(self.msg)


class ChimeraModuleNotExistsError(ValueError):
    def __init__(self) -> None:
        self.msg = "The tester have not install any chimera module."
        super().__init__(self.msg)