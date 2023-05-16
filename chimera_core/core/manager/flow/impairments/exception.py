class DistributionNotSetError(ValueError):
    def __init__(self) -> None:
        self.msg = "Distribution have not set yet"
        super().__init__(self.msg)