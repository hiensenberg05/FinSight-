from typing import Optional
from pydantic import BaseModel, ConfigDict


class TransactionBase(BaseModel):
    date: str
    merchant: str
    category: str
    amount: float
    type: str  # 'expense' | 'income'
    channel: Optional[str] = "UPI"
    isAnomaly: Optional[bool] = False
    anomalyReason: Optional[str] = None


class TransactionCreate(TransactionBase):
    account_id: str


class TransactionRead(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: str


class TransactionFilter(BaseModel):
    category: Optional[str] = None
    search: Optional[str] = None
    is_anomaly: Optional[bool] = None
    limit: int = 100
    offset: int = 0
