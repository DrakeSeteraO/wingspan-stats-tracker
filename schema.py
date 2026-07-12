from pydantic import BaseModel
from typing import List

class StatsRequest(BaseModel):
    score: str
    interval: str
    players: List[str]
    handler: str