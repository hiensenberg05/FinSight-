import uuid
from datetime import datetime, date, timezone
from typing import Optional, List
from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    Boolean,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Text,
    Index,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ==========================================
# 5. Core Identity and Account Tables
# ==========================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), default="Aarav Mehta")
    preferred_language: Mapped[str] = mapped_column(String(16), default="en")
    base_currency: Mapped[str] = mapped_column(String(3), default="INR")
    persona_type: Mapped[str] = mapped_column(String(32), default="tech_professional")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    accounts: Mapped[List["BankAccount"]] = relationship("BankAccount", back_populates="user", cascade="all, delete-orphan")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    budgets: Mapped[List["Budget"]] = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    savings_goals: Mapped[List["SavingsGoal"]] = relationship("SavingsGoal", back_populates="user", cascade="all, delete-orphan")
    bills: Mapped[List["RecurringPayment"]] = relationship("RecurringPayment", back_populates="user", cascade="all, delete-orphan")
    import_jobs: Mapped[List["ImportJob"]] = relationship("ImportJob", back_populates="user", cascade="all, delete-orphan")


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    institution_name: Mapped[str] = mapped_column(String(120), nullable=False)
    account_label: Mapped[str] = mapped_column(String(120), default="Everyday account")
    account_type: Mapped[str] = mapped_column(String(32), default="savings")
    account_mask: Mapped[str] = mapped_column(String(16), default="4821")
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    balance_minor: Mapped[int] = mapped_column(BigInteger, default=0)
    is_connected: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    user: Mapped["User"] = relationship("User", back_populates="accounts")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="account")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    slug: Mapped[str] = mapped_column(String(96), index=True, nullable=False)
    category_type: Mapped[str] = mapped_column(String(24), default="expense")
    color_hex: Mapped[str] = mapped_column(String(16), default="#8B5CF6")
    is_system: Mapped[bool] = mapped_column(Boolean, default=True)


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    canonical_name: Mapped[str] = mapped_column(String(160), nullable=False)
    normalized_key: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    default_category_slug: Mapped[Optional[str]] = mapped_column(String(96), nullable=True)

    aliases: Mapped[List["MerchantAlias"]] = relationship("MerchantAlias", back_populates="merchant", cascade="all, delete-orphan")


class MerchantAlias(Base):
    __tablename__ = "merchant_aliases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    merchant_id: Mapped[str] = mapped_column(String(36), ForeignKey("merchants.id", ondelete="CASCADE"), index=True, nullable=False)
    alias_pattern: Mapped[str] = mapped_column(String(200), nullable=False)
    match_type: Mapped[str] = mapped_column(String(16), default="contains")
    priority: Mapped[int] = mapped_column(Integer, default=10)

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="aliases")


class UserMerchantRule(Base):
    __tablename__ = "user_merchant_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    match_value: Mapped[str] = mapped_column(String(200), nullable=False)
    category_slug: Mapped[str] = mapped_column(String(96), nullable=False)
    payment_mode: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)


# ==========================================
# 6. Import and Transaction Tables
# ==========================================

class ImportJob(Base):
    __tablename__ = "import_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    account_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("bank_accounts.id", ondelete="SET NULL"), nullable=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="completed")
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    committed_rows: Mapped[int] = mapped_column(Integer, default=0)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    user: Mapped["User"] = relationship("User", back_populates="import_jobs")
    rows: Mapped[List["ImportRow"]] = relationship("ImportRow", back_populates="import_job", cascade="all, delete-orphan")


class ImportRow(Base):
    __tablename__ = "import_rows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    import_job_id: Mapped[str] = mapped_column(String(36), ForeignKey("import_jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_values: Mapped[str] = mapped_column(Text, nullable=False)
    validation_status: Mapped[str] = mapped_column(String(16), default="valid")
    transaction_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)

    import_job: Mapped["ImportJob"] = relationship("ImportJob", back_populates="rows")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("idx_transactions_user_date", "user_id", "transaction_date"),
        Index("idx_transactions_user_cat_date", "user_id", "category_name", "transaction_date"),
        Index("idx_transactions_user_merch_date", "user_id", "merchant_name", "transaction_date"),
        Index("idx_transactions_account_date", "account_id", "transaction_date"),
        CheckConstraint("amount_minor != 0", name="chk_nonzero_amount"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("bank_accounts.id", ondelete="CASCADE"), index=True, nullable=False)
    import_job_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("import_jobs.id", ondelete="SET NULL"), nullable=True)
    transaction_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    merchant_name: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    category_name: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)  # Exact paise
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    transaction_kind: Mapped[str] = mapped_column(String(24), default="expense")
    payment_mode: Mapped[str] = mapped_column(String(32), default="UPI")
    description_original: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_internal_transfer: Mapped[bool] = mapped_column(Boolean, default=False)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, default=False)
    anomaly_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    user: Mapped["User"] = relationship("User", back_populates="transactions")
    account: Mapped["BankAccount"] = relationship("BankAccount", back_populates="transactions")


class TransactionLink(Base):
    __tablename__ = "transaction_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    from_transaction_id: Mapped[str] = mapped_column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    to_transaction_id: Mapped[str] = mapped_column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    link_type: Mapped[str] = mapped_column(String(24), default="transfer_pair")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


# ==========================================
# 7. Budgets, Goals and Recurring Payments
# ==========================================

class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        Index("idx_budgets_user_cat", "user_id", "category_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    category_name: Mapped[str] = mapped_column(String(80), nullable=False)
    limit_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    period: Mapped[str] = mapped_column(String(32), default="monthly")
    alert_threshold_pct: Mapped[float] = mapped_column(Float, default=80.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    user: Mapped["User"] = relationship("User", back_populates="budgets")


class SavingsGoal(Base):
    __tablename__ = "savings_goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    target_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    current_amount_minor: Mapped[int] = mapped_column(BigInteger, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    color_hex: Mapped[str] = mapped_column(String(16), default="#06B6D4")
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    user: Mapped["User"] = relationship("User", back_populates="savings_goals")


class RecurringPayment(Base):
    __tablename__ = "recurring_payments"
    __table_args__ = (
        Index("idx_recurring_user_status", "user_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category_name: Mapped[str] = mapped_column(String(80), default="Subscription")
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    due_date_str: Mapped[str] = mapped_column(String(64), nullable=False)
    days_left: Mapped[int] = mapped_column(Integer, default=7)
    auto_pay: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(16), default="scheduled")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    user: Mapped["User"] = relationship("User", back_populates="bills")


# ==========================================
# 8. Anomaly and Forecasting Tables
# ==========================================

class Anomaly(Base):
    __tablename__ = "anomalies"
    __table_args__ = (
        Index("idx_anomalies_user_status_date", "user_id", "status", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=True)
    anomaly_type: Mapped[str] = mapped_column(String(32), default="amount_spike")
    severity: Mapped[str] = mapped_column(String(12), default="medium")
    score: Mapped[float] = mapped_column(Float, default=0.85)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class ForecastRun(Base):
    __tablename__ = "forecast_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    forecast_type: Mapped[str] = mapped_column(String(24), default="cash_flow")
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    model_name: Mapped[str] = mapped_column(String(64), default="Prophet/Holt-Winters")
    model_version: Mapped[str] = mapped_column(String(32), default="1.0.0")
    status: Mapped[str] = mapped_column(String(16), default="completed")
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    points: Mapped[List["ForecastPointItem"]] = relationship("ForecastPointItem", back_populates="forecast_run", cascade="all, delete-orphan")


class ForecastPointItem(Base):
    __tablename__ = "forecast_points"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    forecast_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("forecast_runs.id", ondelete="CASCADE"), index=True, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    lower_bound_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    upper_bound_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    forecast_run: Mapped["ForecastRun"] = relationship("ForecastRun", back_populates="points")


# ==========================================
# 9. Voice, Notification and Slack Tables
# ==========================================

class VoiceSession(Base):
    __tablename__ = "voice_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="en")
    status: Mapped[str] = mapped_column(String(16), default="active")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    turns: Mapped[List["VoiceTurn"]] = relationship("VoiceTurn", back_populates="session", cascade="all, delete-orphan")


class VoiceTurn(Base):
    __tablename__ = "voice_turns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("voice_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    transcript_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tool_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    tool_args: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tool_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    session: Mapped["VoiceSession"] = relationship("VoiceSession", back_populates="turns")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), default="budget_alert")
    status: Mapped[str] = mapped_column(String(16), default="unread")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class SlackLink(Base):
    __tablename__ = "slack_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    team_id: Mapped[str] = mapped_column(String(64), nullable=False)
    slack_user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


# ==========================================
# 10. Operational Action & Sentinel Tables
# ==========================================

class ActionRequest(Base):
    """
    Two-phase human-in-the-loop action proposals.
    Requires explicit user confirmation before executing state mutations.
    """
    __tablename__ = "action_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)  # set_category_budget, create_savings_goal, etc.
    status: Mapped[str] = mapped_column(String(24), default="pending", index=True)  # pending, confirmed, executed, cancelled, expired
    target_resource_type: Mapped[str] = mapped_column(String(48), nullable=False)  # budget, savings_goal, transaction, recurring_payment
    target_resource_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    parameters_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON payload
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ActionAuditLog(Base):
    """
    Immutable audit log for all financial ledger and workspace mutations.
    """
    __tablename__ = "action_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    action_id: Mapped[str] = mapped_column(String(36), ForeignKey("action_requests.id", ondelete="CASCADE"), index=True, nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(64), default="user")
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    before_state_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    after_state_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class FinancialAlert(Base):
    """
    Proactive sentinel financial alerts and threshold breaches.
    """
    __tablename__ = "financial_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    alert_type: Mapped[str] = mapped_column(String(48), nullable=False)  # budget_threshold, anomaly_spike, upcoming_bill
    severity: Mapped[str] = mapped_column(String(16), default="warning")  # info, warning, critical
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    event_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class ProcessedDomainEvent(Base):
    """
    Idempotent event processing tracker.
    """
    __tablename__ = "processed_domain_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class ConversationEpisode(Base):
    """
    Episodic memory store capturing cross-session user decisions, commitments,
    and financial milestones.
    """
    __tablename__ = "conversation_episodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    session_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)
    episode_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # budget_commitment, goal_milestone, spending_preference, decision_record
    topic: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    facts_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON payload of verified parameters
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


