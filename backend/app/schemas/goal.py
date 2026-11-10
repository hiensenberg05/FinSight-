from pydantic import BaseModel, ConfigDict


class GoalBase(BaseModel):
    name: str
    targetAmount: float
    currentAmount: float = 0.0
    color: str = "#06B6D4"


class GoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    currentAmount: float
    targetAmount: float
    percentage: int
    color: str
