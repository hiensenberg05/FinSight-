from pydantic import BaseModel, ConfigDict


class BillBase(BaseModel):
    name: str
    category: str
    amount: float
    dueDate: str
    daysLeft: int
    autoPay: bool = False
    status: str = "scheduled"


class BillRead(BillBase):
    model_config = ConfigDict(from_attributes=True)

    id: str


class BillAutoPayUpdate(BaseModel):
    autoPay: bool
