from pydantic import BaseModel, ConfigDict


class AccountBase(BaseModel):
    name: str
    bankName: str
    accountNumberMask: str = "4821"
    accountType: str = "savings"
    currency: str = "₹"
    balance: float = 0.0
    isConnected: bool = True


class AccountCreate(AccountBase):
    pass


class AccountRead(AccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
