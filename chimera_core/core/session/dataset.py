from typing import Optional

from pydantic import BaseModel
from xoa_driver import enums


class ModuleConfig(BaseModel):
    comment: Optional[str] = None
    tx_clock_source: Optional[enums.TXClockSource] = None
    tx_clock_status: Optional[enums.TXClockStatus] = None


class LatencyJitterConfigDistribution(BaseModel):
    constant_delay: Optional[float] = None


class LatencyJitterConfigSchedule(BaseModel):
    duration: Optional[int] = None
    period: Optional[int] = None

class LatencyJitterConfigMain(BaseModel):
    distribution: LatencyJitterConfigDistribution
    schedule: LatencyJitterConfigSchedule
    # ??? status is_enable?
