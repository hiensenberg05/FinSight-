from pydantic import BaseModel, ConfigDict


class BudgetBase(BaseModel):
    category: str
    spent: float = 0.0
    limit: float
    period: str = "Feb 2025"


class BudgetCreate(BaseModel):
    category_name: str
    limit: float
    period: str = "monthly"


class BudgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str
    spent: float
    limit: float
    period: str
