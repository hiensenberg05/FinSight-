from typing import List, Optional
from pydantic import BaseModel
from backend.app.schemas.analytics import CategorySpending


class QuickAction(BaseModel):
    label: str
    action: str
    primary: Optional[bool] = False


class VoiceQueryRequest(BaseModel):
    query: str
    language: str = "en"
    session_id: Optional[str] = None


class VoiceQueryResponse(BaseModel):
    text: str
    actionChips: Optional[List[str]] = None
    chartData: Optional[List[CategorySpending]] = None
    chartTitle: Optional[str] = None
    quickActions: Optional[List[QuickAction]] = None
    audioBase64: Optional[str] = None
