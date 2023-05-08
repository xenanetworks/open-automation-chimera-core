from typing import Iterable


class InvalidChimeraResourceError(ValueError):
    def __init__(self, resource: str) -> None:
        self.msg = f"Only accept chimera {resource}."
        super().__init__(self.msg)

class InvalidDistributionError(ValueError):
    def __init__(self, distributions: Iterable[str]) -> None:
        self.msg = f"Only co-working with: [{','.join(distributions)}]."
        super().__init__(self.msg)