"""
Standard Financial Tool Response Contract and Data Provenance Schemas.
Every tool execution generates deterministic evidence and audit provenance.
No hallucinated numbers or fake references.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class EvidenceItem(BaseModel):
    """
    Granular database transaction provenance item.
    Directly references verified SQLite/Postgres ledger records.
    """
    transaction_id: str = Field(..., description="Unique transaction ID from DB")
    account_reference: str = Field(..., description="Institution and masked account number, e.g. HDFC-XXXX-4821")
    date: str = Field(..., description="ISO 8601 transaction date (YYYY-MM-DD)")
    merchant: str = Field(..., description="Counterparty or merchant name")
    amount_minor: int = Field(..., description="Monetary value in integer paise")
    amount_formatted: str = Field(..., description="Human-readable currency amount, e.g. ₹5,800.00")
    currency: str = Field(default="INR", description="ISO currency code")
    category: str = Field(..., description="Assigned category name")
    payment_mode: Optional[str] = Field(default="UPI", description="Payment instrument")
    source_import_id: Optional[str] = Field(default=None, description="Original statement import job reference")
    is_anomaly: bool = Field(default=False, description="Flagged as spending outlier")
    anomaly_reason: Optional[str] = Field(default=None, description="Anomaly explanation if flagged")


class ResponseMetadata(BaseModel):
    """
    Provenance calculation metadata for auditability and explainability.
    """
    calculation_period: str = Field(..., description="Period evaluated, e.g. 'Feb 2025 vs Jan 2025'")
    aggregation_methodology: str = Field(
        ...,
        description="Deterministic SQL aggregation methodology, e.g. 'SUM(abs(amount_minor)) GROUP BY category_name'"
    )
    record_count: int = Field(..., description="Total database rows evaluated in this calculation")
    verified_ledger: bool = Field(default=True, description="Guaranteed grounded in relational ledger")
    executed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC timestamp of query execution"
    )


class ToolResponseContract(BaseModel):
    """
    Standard envelope returned by all deterministic financial tools.
    """
    success: bool = True
    summary: str = Field(..., description="Concise textual summary of findings")
    data: Dict[str, Any] = Field(default_factory=dict, description="Structured numerical and aggregated payload")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Audit trail of exact DB transactions")
    metadata: ResponseMetadata = Field(..., description="Methodology and audit record counts")
