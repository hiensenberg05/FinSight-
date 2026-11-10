from typing import List, Optional
from pydantic import BaseModel


class FinancialHealthMetrics(BaseModel):
    score: int  # 0 - 100
    rating: str  # 'Poor' | 'Fair' | 'Good' | 'Excellent'
    summary: str
    availableBalance: float
    monthlySavings: float
    pendingBills: float
    period: str


class CategorySpending(BaseModel):
    name: str
    amount: float
    currency: str = "₹"
    percentage: int
    color: str


class ForecastPoint(BaseModel):
    date: str
    month: Optional[str] = None
    actualAmount: Optional[float] = None
    predictedAmount: Optional[float] = None
    predictedSpend: float
    projectedBalance: Optional[float] = None
    lowerBound: Optional[float] = None
    upperBound: Optional[float] = None
    upperConfidence: float
    lowerConfidence: float


class IngestionResult(BaseModel):
    success: bool
    importedRows: int
    message: str
    bank: str
