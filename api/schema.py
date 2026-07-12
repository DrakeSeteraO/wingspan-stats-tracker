from pydantic import BaseModel
from typing import List, Union, Optional

class TrendRequest(BaseModel):
    score: str
    interval: str
    players: List[str]
    handler: str
    

class PlayerStat(BaseModel):
    player: str
    
    # We define all possible frontend metrics as optional floats.
    # Using floats safely handles averages (e.g., 24.5 points).
    totalPoints: Optional[float] = None
    bird: Optional[float] = None
    bonus_card: Optional[float] = None
    end_of_round_goals: Optional[float] = None
    goals: Optional[float] = None
    eggs: Optional[float] = None
    food: Optional[float] = None
    tucked: Optional[float] = None
    nectar: Optional[float] = None


class TrendRecord(BaseModel):
    # Union allows the date to be an ISO string ("2026-07-12") or an integer ID for individual games
    date: Union[str, int]
    results: List[PlayerStat]