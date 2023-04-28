class InvalidChimeraResourceError(ValueError):
    def __init__(self, resource: str) -> None:
        self.msg = f"Only accept chimera {resource}."
        super().__init__(self.msg)