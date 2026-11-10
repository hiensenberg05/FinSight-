# FinSight --- Data Schema and Synthetic Data Specification

**Document:** `data_schema.md`\
**Status:** Proposed logical schema --- review against implementation
migrations\
**Database:** PostgreSQL\
**Primary design:** Multi-user personal finance, exact monetary
representation, import traceability

------------------------------------------------------------------------

## 1. Purpose and scope

This document defines the proposed relational data model for FinSight
and the synthetic datasets required for development, testing and
hackathon demonstration.

It covers:

-   User and account ownership.
-   CSV import jobs and row-level traceability.
-   Canonical transaction representation.
-   Merchant and category normalization.
-   Budgets and savings goals.
-   Recurring-payment observations.
-   Anomaly detection and review decisions.
-   Forecast runs and forecast outputs.
-   Voice conversation metadata.
-   Notifications and Slack identity linkage.
-   Synthetic data generation, validation and evaluation splits.

This is a logical design. The actual SQLAlchemy models and Alembic
migrations are the implementation source of truth once created.

## 2. Database design principles

1.  PostgreSQL is the authoritative store for financial records.
2.  Every user-owned entity has a `user_id` ownership boundary, directly
    or through a parent relation.
3.  Store money as integer minor units plus ISO currency code; do not
    use floating-point types.
4.  Preserve source statement values and row references for
    auditability.
5.  Internal transfers, refunds and reversals must not be treated as
    ordinary expenses.
6.  Duplicate detection should flag candidates; it must not silently
    delete records.
7.  Category assignments need confidence and provenance.
8.  Store model version and assumptions for anomaly and forecast
    outputs.
9.  Use `TIMESTAMPTZ` for instants; use `DATE` for statement transaction
    dates where no reliable time exists.
10. Use database constraints for invariants that can be enforced
    relationally.
11. Use indexes based on real query patterns; do not index every column.
12. Use soft deletion only where a recovery/audit requirement justifies
    it. Define retention separately.

------------------------------------------------------------------------

## 3. Entity relationship overview

``` mermaid
erDiagram
    USERS ||--o{ BANK_ACCOUNTS : owns
    USERS ||--o{ IMPORT_JOBS : creates
    BANK_ACCOUNTS ||--o{ TRANSACTIONS : contains
    IMPORT_JOBS ||--o{ IMPORT_ROWS : parses
    IMPORT_ROWS ||--o| TRANSACTIONS : creates
    USERS ||--o{ TRANSACTIONS : owns
    MERCHANTS ||--o{ TRANSACTIONS : matches
    CATEGORIES ||--o{ TRANSACTIONS : classifies
    USERS ||--o{ BUDGETS : configures
    CATEGORIES ||--o{ BUDGETS : scopes
    USERS ||--o{ SAVINGS_GOALS : defines
    USERS ||--o{ RECURRING_PAYMENTS : tracks
    MERCHANTS ||--o{ RECURRING_PAYMENTS : associated
    USERS ||--o{ ANOMALIES : receives
    TRANSACTIONS ||--o{ ANOMALIES : evidence
    USERS ||--o{ FORECAST_RUNS : requests
    FORECAST_RUNS ||--o{ FORECAST_POINTS : produces
    USERS ||--o{ VOICE_SESSIONS : starts
    VOICE_SESSIONS ||--o{ VOICE_TURNS : contains
    USERS ||--o{ NOTIFICATIONS : receives
    USERS ||--o{ SLACK_LINKS : connects
```

The diagram is conceptual. Some optional relationships (such as
transaction-to-import-row) should be nullable for manually created or
migrated records.

------------------------------------------------------------------------

## 4. PostgreSQL conventions

### 4.1 Common types

  -----------------------------------------------------------------------
  Concept                             Recommended type
  ----------------------------------- -----------------------------------
  Primary identifiers                 UUID

  User-facing external IDs            UUID or opaque string

  Money                               BIGINT minor units

  Currency                            CHAR(3) ISO 4217 code

  Date without time                   DATE

  Timestamp                           TIMESTAMPTZ

  Confidence / statistical score      NUMERIC or DOUBLE PRECISION,
                                      depending on use

  Counts                              INTEGER or BIGINT

  Flexible provider/import metadata   JSONB, bounded and validated

  Status                              VARCHAR with CHECK constraint or
                                      PostgreSQL enum

  Hash/checksum                       CHAR(64) for SHA-256 hex digest
  -----------------------------------------------------------------------

Use UTC for stored instants. Keep a user timezone preference for
date-window interpretation and scheduled notifications.

### 4.2 Monetary sign convention

For canonical transactions:

-   Positive `amount_minor`: money entering the account.
-   Negative `amount_minor`: money leaving the account.
-   `transaction_kind` describes semantic meaning: `income`, `expense`,
    `transfer`, `refund`, `reversal`, `fee`, `interest`, `unknown`.

Do not rely on sign alone to determine spending. For example, a transfer
outflow is negative but is not consumption. Refunds may be positive but
should generally reduce net spending for the relevant category/reporting
policy.

For split debit/credit source columns, normalize to the signed
convention. Retain raw source values in import-row metadata for
traceability.

### 4.3 Currency precision

Store integer minor units and currency code. Do not assume every
currency has two decimal places. Implement a currency exponent utility
and a supported-currency policy. For the hackathon demo, INR may be the
primary currency, but the schema should not silently interpret every
currency as paise.

### 4.4 Ownership

Every user-owned query must filter by the authenticated `user_id`.
Prefer composite uniqueness and foreign-key patterns that prevent
cross-user references where practical.

------------------------------------------------------------------------

## 5. Core identity and account tables

### 5.1 `users`

  -----------------------------------------------------------------------
  Column                  Type                    Constraints / meaning
  ----------------------- ----------------------- -----------------------
  `id`                    UUID                    PK

  `email`                 CITEXT or VARCHAR(320)  Unique, normalized

  `password_hash`         TEXT                    Nullable if external
                                                  auth is used

  `display_name`          VARCHAR(120)            Optional

  `preferred_language`    VARCHAR(16)             Optional, validated
                                                  against supported set

  `timezone`              VARCHAR(64)             IANA timezone, default
                                                  UTC

  `base_currency`         CHAR(3)                 ISO currency code

  `is_active`             BOOLEAN                 NOT NULL, default true

  `created_at`            TIMESTAMPTZ             NOT NULL

  `updated_at`            TIMESTAMPTZ             NOT NULL
  -----------------------------------------------------------------------

Security: - Never store plaintext passwords. - Do not expose password
hashes through APIs. - Email uniqueness should be case-insensitive.

### 5.2 `bank_accounts`

  -------------------------------------------------------------------------
  Column                    Type                    Constraints / meaning
  ------------------------- ----------------------- -----------------------
  `id`                      UUID                    PK

  `user_id`                 UUID                    FK users, NOT NULL

  `institution_name`        VARCHAR(120)            Optional

  `account_label`           VARCHAR(120)            User-facing alias

  `account_type`            VARCHAR(32)             savings, current,
                                                    credit_card, cash,
                                                    wallet, other

  `account_mask`            VARCHAR(16)             Optional masked suffix
                                                    only

  `currency`                CHAR(3)                 NOT NULL

  `opening_balance_minor`   BIGINT                  Optional

  `is_active`               BOOLEAN                 NOT NULL, default true

  `created_at`              TIMESTAMPTZ             NOT NULL

  `updated_at`              TIMESTAMPTZ             NOT NULL
  -------------------------------------------------------------------------

Constraints: - `UNIQUE (id, user_id)` to support ownership-aware
composite foreign keys. - No full bank account number, card number, CVV,
PIN or banking password. - Account opening balance semantics and date
must be explicit if used in balance forecasts.

### 5.3 `categories`

System category master, optionally extended by user-defined categories.

  -----------------------------------------------------------------------
  Column                  Type                    Constraints / meaning
  ----------------------- ----------------------- -----------------------
  `id`                    UUID                    PK

  `user_id`               UUID                    Nullable; NULL means
                                                  system category

  `name`                  VARCHAR(80)             NOT NULL

  `slug`                  VARCHAR(96)             Normalized

  `parent_id`             UUID                    Optional self-FK

  `category_type`         VARCHAR(24)             income, expense,
                                                  transfer, adjustment

  `is_system`             BOOLEAN                 NOT NULL

  `is_active`             BOOLEAN                 NOT NULL

  `created_at`            TIMESTAMPTZ             NOT NULL
  -----------------------------------------------------------------------

Constraints: - Unique system slug where `user_id IS NULL`. - Unique
`(user_id, slug)` for user-owned categories. - Validate parent category
ownership and avoid cycles in application logic. - Suggested system
expense categories: Housing, Groceries, Dining, Transport, Shopping,
Utilities, Healthcare, Education, Entertainment, Travel, Personal Care,
Subscriptions, Fees, Insurance, Other. - Suggested income categories:
Salary, Freelance, Interest, Refund, Other Income. - Transfers should be
represented as a transaction kind, not ordinary spending categories.

### 5.4 `merchants`

Global canonical merchant dictionary. Avoid storing user-specific
sensitive descriptions here.

  Column                  Type           Constraints / meaning
  ----------------------- -------------- ------------------------
  `id`                    UUID           PK
  `canonical_name`        VARCHAR(160)   NOT NULL
  `normalized_key`        VARCHAR(180)   NOT NULL, unique
  `default_category_id`   UUID           Optional FK categories
  `created_at`            TIMESTAMPTZ    NOT NULL
  `updated_at`            TIMESTAMPTZ    NOT NULL

A global merchant master must not contain raw user transaction
descriptions or personal information.

### 5.5 `merchant_aliases`

  Column            Type           Constraints / meaning
  ----------------- -------------- ------------------------
  `id`              UUID           PK
  `merchant_id`     UUID           FK merchants
  `alias_pattern`   VARCHAR(200)   Normalized alias
  `match_type`      VARCHAR(16)    exact, prefix, regex
  `priority`        INTEGER        Higher evaluated first
  `created_at`      TIMESTAMPTZ    NOT NULL

Regex patterns must be curated and safe. For MVP, exact and prefix
matching are preferable.

### 5.6 `user_merchant_rules`

  Column           Type           Constraints / meaning
  ---------------- -------------- ---------------------------------------
  `id`             UUID           PK
  `user_id`        UUID           FK users
  `match_value`    VARCHAR(200)   Normalized source-description pattern
  `match_type`     VARCHAR(16)    exact, contains, prefix
  `merchant_id`    UUID           Optional FK merchants
  `category_id`    UUID           Optional category FK
  `payment_mode`   VARCHAR(32)    Optional
  `created_at`     TIMESTAMPTZ    NOT NULL
  `updated_at`     TIMESTAMPTZ    NOT NULL

User-specific mappings take precedence over global defaults. Validate
ownership of referenced categories.

------------------------------------------------------------------------

## 6. Import and transaction tables

### 6.1 `import_jobs`

One record per uploaded statement/import attempt.

  -------------------------------------------------------------------------
  Column                   Type                    Constraints / meaning
  ------------------------ ----------------------- ------------------------
  `id`                     UUID                    PK

  `user_id`                UUID                    FK users, NOT NULL

  `account_id`             UUID                    Optional FK
                                                   bank_accounts

  `original_filename`      VARCHAR(255)            Sanitized display name

  `storage_key`            TEXT                    Private object storage
                                                   key

  `file_sha256`            CHAR(64)                Checksum

  `file_size_bytes`        BIGINT                  Positive

  `detected_encoding`      VARCHAR(40)             Optional

  `mapping_config`         JSONB                   Validated
                                                   source-to-canonical
                                                   mapping

  `status`                 VARCHAR(24)             uploaded, previewing,
                                                   awaiting_confirmation,
                                                   processing, completed,
                                                   failed, cancelled

  `total_rows`             INTEGER                 Optional

  `valid_rows`             INTEGER                 Optional

  `invalid_rows`           INTEGER                 Optional

  `duplicate_candidates`   INTEGER                 Optional

  `committed_rows`         INTEGER                 Optional

  `error_summary`          JSONB                   Sanitized summary

  `idempotency_key`        VARCHAR(128)            Unique per user/request

  `created_at`             TIMESTAMPTZ             NOT NULL

  `completed_at`           TIMESTAMPTZ             Optional
  -------------------------------------------------------------------------

Constraints: - `UNIQUE (user_id, idempotency_key)` where idempotency key
is not NULL. - File size and row limits enforced. - Storage key must
never be publicly accessible. - Do not store the full raw CSV inside
JSONB.

### 6.2 `import_rows`

Row-level parse and validation record. For large imports, retention may
be limited after successful commit.

  Column                Type          Constraints / meaning
  --------------------- ------------- ---------------------------------------
  `id`                  UUID          PK
  `import_job_id`       UUID          FK import_jobs
  `row_number`          INTEGER       Source row number
  `raw_values`          JSONB         Sanitized source row values
  `normalized_values`   JSONB         Candidate canonical values
  `validation_status`   VARCHAR(16)   valid, invalid, warning, skipped
  `validation_errors`   JSONB         Array of structured errors
  `transaction_id`      UUID          Optional FK transactions after commit
  `created_at`          TIMESTAMPTZ   NOT NULL

Constraints: - `UNIQUE (import_job_id, row_number)`. - Do not persist
unbounded cell values; enforce field length limits. - Sanitize secrets
or account identifiers if present in source files.

### 6.3 `transactions`

Canonical financial transaction table.

  --------------------------------------------------------------------------
  Column                     Type                    Constraints / meaning
  -------------------------- ----------------------- -----------------------
  `id`                       UUID                    PK

  `user_id`                  UUID                    FK users, NOT NULL

  `account_id`               UUID                    FK bank_accounts, NOT
                                                     NULL

  `import_job_id`            UUID                    Optional FK import_jobs

  `source_row_id`            UUID                    Optional FK import_rows

  `source_transaction_ref`   VARCHAR(160)            Optional
                                                     statement-provided ID

  `transaction_date`         DATE                    NOT NULL

  `posted_at`                TIMESTAMPTZ             Optional

  `description_original`     TEXT                    Original statement text

  `description_normalized`   TEXT                    Normalized text

  `merchant_id`              UUID                    Optional FK merchants

  `category_id`              UUID                    Optional FK categories

  `amount_minor`             BIGINT                  Signed; NOT NULL

  `currency`                 CHAR(3)                 NOT NULL

  `transaction_kind`         VARCHAR(24)             income, expense,
                                                     transfer, refund,
                                                     reversal, fee,
                                                     interest, unknown

  `payment_mode`             VARCHAR(32)             upi, card,
                                                     bank_transfer, cash,
                                                     wallet, cheque, other,
                                                     unknown

  `category_confidence`      NUMERIC(5,4)            0.0--1.0, nullable

  `category_source`          VARCHAR(24)             user_rule,
                                                     merchant_rule,
                                                     classifier, llm,
                                                     manual, unknown

  `is_internal_transfer`     BOOLEAN                 NOT NULL, default false

  `transfer_group_id`        UUID                    Optional self/group
                                                     reference

  `duplicate_group_id`       UUID                    Optional

  `review_status`            VARCHAR(20)             unreviewed, confirmed,
                                                     excluded

  `notes`                    TEXT                    Optional user
                                                     annotation

  `created_at`               TIMESTAMPTZ             NOT NULL

  `updated_at`               TIMESTAMPTZ             NOT NULL
  --------------------------------------------------------------------------

Important constraints and indexes: -
`CHECK (category_confidence IS NULL OR category_confidence BETWEEN 0 AND 1)`. -
Index `(user_id, transaction_date DESC)`. - Index
`(user_id, category_id, transaction_date DESC)`. - Index
`(user_id, merchant_id, transaction_date DESC)`. - Index
`(account_id, transaction_date DESC)`. - Optional partial index for
unreviewed records. - Use composite foreign keys where needed to ensure
account and user ownership agree. - Do not create a uniqueness
constraint on date+amount+description alone; legitimate recurring
transactions can share those values. - Use source IDs/checksums and
idempotent import logic to prevent duplicate imports. - Transfers
between own accounts may be represented as two linked transactions in
one transfer group; do not count either as consumption. - Refund and
reversal linkage may use a separate optional reference or relationship
table if required by the implementation.

### 6.4 `transaction_links` (optional but recommended)

For relationships between related transactions, such as transfer pairs,
refund-to-original or reversal-to-original.

  -----------------------------------------------------------------------
  Column                  Type                    Constraints / meaning
  ----------------------- ----------------------- -----------------------
  `id`                    UUID                    PK

  `user_id`               UUID                    FK users

  `from_transaction_id`   UUID                    FK transactions

  `to_transaction_id`     UUID                    FK transactions

  `link_type`             VARCHAR(24)             transfer_pair,
                                                  refund_of, reversal_of,
                                                  duplicate_candidate

  `confidence`            NUMERIC(5,4)            Optional 0--1

  `created_at`            TIMESTAMPTZ             NOT NULL
  -----------------------------------------------------------------------

Prevent self-links and enforce both transactions belong to the same
user.

------------------------------------------------------------------------

## 7. Budgets, goals and recurring payments

### 7.1 `budgets`

  Column                  Type           Constraints / meaning
  ----------------------- -------------- --------------------------------------
  `id`                    UUID           PK
  `user_id`               UUID           FK users
  `category_id`           UUID           Optional; NULL may mean total budget
  `name`                  VARCHAR(120)   NOT NULL
  `period_type`           VARCHAR(16)    monthly, weekly, custom
  `amount_minor`          BIGINT         Positive
  `currency`              CHAR(3)        NOT NULL
  `start_date`            DATE           NOT NULL
  `end_date`              DATE           Optional
  `alert_threshold_pct`   NUMERIC(5,2)   Optional
  `is_active`             BOOLEAN        NOT NULL
  `created_at`            TIMESTAMPTZ    NOT NULL
  `updated_at`            TIMESTAMPTZ    NOT NULL

Budget actuals should generally be computed from canonical transactions,
not stored as mutable totals. Define treatment of refunds, transfers and
excluded transactions.

### 7.2 `savings_goals`

  ------------------------------------------------------------------------
  Column                   Type                    Constraints / meaning
  ------------------------ ----------------------- -----------------------
  `id`                     UUID                    PK

  `user_id`                UUID                    FK users

  `name`                   VARCHAR(120)            NOT NULL

  `target_amount_minor`    BIGINT                  Positive

  `current_amount_minor`   BIGINT                  Non-negative;
                                                   user-entered or
                                                   reconciled

  `currency`               CHAR(3)                 NOT NULL

  `target_date`            DATE                    Optional

  `start_date`             DATE                    NOT NULL

  `status`                 VARCHAR(16)             active, achieved,
                                                   paused, cancelled

  `created_at`             TIMESTAMPTZ             NOT NULL

  `updated_at`             TIMESTAMPTZ             NOT NULL
  ------------------------------------------------------------------------

Do not imply the platform can observe all savings held outside imported
accounts. Clearly identify whether current amount is user-entered or
derived from linked records.

### 7.3 `recurring_payments`

A detected or user-confirmed recurring-payment pattern, not a guaranteed
future debit.

  -------------------------------------------------------------------------
  Column                    Type                    Constraints / meaning
  ------------------------- ----------------------- -----------------------
  `id`                      UUID                    PK

  `user_id`                 UUID                    FK users

  `merchant_id`             UUID                    Optional FK merchants

  `description_pattern`     VARCHAR(200)            Optional

  `expected_amount_minor`   BIGINT                  Optional

  `currency`                CHAR(3)                 NOT NULL

  `frequency`               VARCHAR(16)             weekly, monthly,
                                                    quarterly, yearly,
                                                    irregular

  `next_expected_date`      DATE                    Optional estimate

  `confidence`              NUMERIC(5,4)            0--1

  `detection_source`        VARCHAR(20)             rule, user_confirmed

  `status`                  VARCHAR(16)             detected, confirmed,
                                                    dismissed, inactive

  `created_at`              TIMESTAMPTZ             NOT NULL

  `updated_at`              TIMESTAMPTZ             NOT NULL
  -------------------------------------------------------------------------

A separate join table `recurring_payment_transactions` should link
observed transactions to the recurring pattern and record the evidence.
Do not claim a future payment is certain.

------------------------------------------------------------------------

## 8. Anomaly and forecasting tables

### 8.1 `anomalies`

  ---------------------------------------------------------------------------
  Column                    Type                    Constraints / meaning
  ------------------------- ----------------------- -------------------------
  `id`                      UUID                    PK

  `user_id`                 UUID                    FK users

  `transaction_id`          UUID                    Optional FK transactions

  `anomaly_type`            VARCHAR(32)             amount_spike,
                                                    category_spike,
                                                    duplicate_candidate,
                                                    frequency_change,
                                                    recurring_amount_change

  `severity`                VARCHAR(12)             low, medium, high

  `score`                   NUMERIC(8,5)            Optional

  `evidence`                JSONB                   Bounded, explainable
                                                    evidence

  `baseline_window_start`   DATE                    Optional

  `baseline_window_end`     DATE                    Optional

  `detector_name`           VARCHAR(64)             NOT NULL

  `detector_version`        VARCHAR(32)             NOT NULL

  `status`                  VARCHAR(16)             open, reviewed, dismissed

  `reviewed_at`             TIMESTAMPTZ             Optional

  `created_at`              TIMESTAMPTZ             NOT NULL
  ---------------------------------------------------------------------------

An anomaly is an investigation signal, not a fraud conclusion. Store the
detector version and evidence so the result can be explained.

### 8.2 `forecast_runs`

  -----------------------------------------------------------------------
  Column                  Type                    Constraints / meaning
  ----------------------- ----------------------- -----------------------
  `id`                    UUID                    PK

  `user_id`               UUID                    FK users

  `forecast_type`         VARCHAR(24)             monthly_expense,
                                                  cash_flow,
                                                  category_expense,
                                                  savings

  `currency`              CHAR(3)                 NOT NULL

  `model_name`            VARCHAR(64)             NOT NULL

  `model_version`         VARCHAR(32)             NOT NULL

  `training_start_date`   DATE                    Optional

  `training_end_date`     DATE                    Optional

  `generated_at`          TIMESTAMPTZ             NOT NULL

  `status`                VARCHAR(16)             completed,
                                                  insufficient_data,
                                                  failed

  `metrics`               JSONB                   Evaluation metrics and
                                                  metadata

  `assumptions`           JSONB                   Bounded, validated
                                                  assumptions
  -----------------------------------------------------------------------

### 8.3 `forecast_points`

  Column                     Type          Constraints / meaning
  -------------------------- ------------- -----------------------
  `id`                       UUID          PK
  `forecast_run_id`          UUID          FK forecast_runs
  `period_start`             DATE          NOT NULL
  `period_end`               DATE          NOT NULL
  `predicted_amount_minor`   BIGINT        NOT NULL
  `lower_bound_minor`        BIGINT        Optional
  `upper_bound_minor`        BIGINT        Optional
  `created_at`               TIMESTAMPTZ   NOT NULL

Constraints: - Unique `(forecast_run_id, period_start, period_end)`. -
Bounds must be consistent when both exist. - Clearly distinguish point
estimates from prediction intervals.

------------------------------------------------------------------------

## 9. Voice, notification and Slack tables

### 9.1 `voice_sessions`

  Column         Type          Constraints / meaning
  -------------- ------------- ------------------------------------
  `id`           UUID          PK
  `user_id`      UUID          FK users
  `language`     VARCHAR(16)   Optional
  `status`       VARCHAR(16)   active, completed, failed, expired
  `started_at`   TIMESTAMPTZ   NOT NULL
  `ended_at`     TIMESTAMPTZ   Optional
  `metadata`     JSONB         Bounded, non-sensitive metadata

### 9.2 `voice_turns`

  Column              Type          Constraints / meaning
  ------------------- ------------- --------------------------------
  `id`                UUID          PK
  `session_id`        UUID          FK voice_sessions
  `request_id`        UUID          Unique request correlation
  `turn_index`        INTEGER       NOT NULL
  `transcript_text`   TEXT          Optional; retention-controlled
  `response_text`     TEXT          Optional; retention-controlled
  `stt_provider`      VARCHAR(32)   Optional
  `tts_provider`      VARCHAR(32)   Optional
  `reasoning_model`   VARCHAR(64)   Optional
  `status`            VARCHAR(16)   completed, failed, cancelled
  `latency_ms`        JSONB         Stage timing metadata
  `created_at`        TIMESTAMPTZ   NOT NULL

Do not store raw audio by default. Transcripts may contain sensitive
information; define retention, access and deletion policy.

### 9.3 `notification_preferences`

  Column                Type          Constraints / meaning
  --------------------- ------------- -----------------------
  `user_id`             UUID          PK/FK users
  `in_app_enabled`      BOOLEAN       NOT NULL
  `slack_enabled`       BOOLEAN       NOT NULL
  `quiet_hours_start`   TIME          Optional
  `quiet_hours_end`     TIME          Optional
  `timezone`            VARCHAR(64)   IANA timezone
  `updated_at`          TIMESTAMPTZ   NOT NULL

### 9.4 `notifications`

  -----------------------------------------------------------------------
  Column                  Type                    Constraints / meaning
  ----------------------- ----------------------- -----------------------
  `id`                    UUID                    PK

  `user_id`               UUID                    FK users

  `notification_type`     VARCHAR(32)             budget_threshold,
                                                  upcoming_payment,
                                                  anomaly, goal_progress,
                                                  summary

  `title`                 VARCHAR(160)            NOT NULL

  `body`                  TEXT                    Minimize sensitive
                                                  details

  `payload`               JSONB                   Bounded reference
                                                  metadata

  `idempotency_key`       VARCHAR(160)            Unique per user

  `status`                VARCHAR(16)             pending, sent, failed,
                                                  dismissed

  `scheduled_at`          TIMESTAMPTZ             Optional

  `sent_at`               TIMESTAMPTZ             Optional

  `created_at`            TIMESTAMPTZ             NOT NULL
  -----------------------------------------------------------------------

### 9.5 `slack_links`

  -----------------------------------------------------------------------
  Column                  Type                    Constraints / meaning
  ----------------------- ----------------------- -----------------------
  `id`                    UUID                    PK

  `user_id`               UUID                    FK users

  `team_id`               VARCHAR(64)             Slack workspace ID

  `slack_user_id`         VARCHAR(64)             Slack user ID

  `encrypted_token_ref`   TEXT                    Secret manager
                                                  reference; not
                                                  plaintext token

  `scopes`                JSONB                   Granted scopes

  `status`                VARCHAR(16)             active, revoked

  `created_at`            TIMESTAMPTZ             NOT NULL

  `updated_at`            TIMESTAMPTZ             NOT NULL
  -----------------------------------------------------------------------

Unique `(team_id, slack_user_id)` where applicable. Store token
references or encrypted credentials, never raw tokens in ordinary logs.

### 9.6 `processed_external_events`

Recommended for Slack idempotency.

  Column                Type           Constraints / meaning
  --------------------- -------------- -------------------------------
  `id`                  UUID           PK
  `provider`            VARCHAR(24)    e.g. slack
  `external_event_id`   VARCHAR(160)   NOT NULL
  `processed_at`        TIMESTAMPTZ    NOT NULL
  `status`              VARCHAR(16)    processing, completed, failed

Unique `(provider, external_event_id)`.

------------------------------------------------------------------------

## 10. Recommended indexes and query patterns

Create indexes based on common access patterns:

  --------------------------------------------------------------------------------
  Query pattern                       Index
  ----------------------------------- --------------------------------------------
  User transaction timeline           `(user_id, transaction_date DESC, id)`

  Category spending by period         `(user_id, category_id, transaction_date)`

  Merchant spend history              `(user_id, merchant_id, transaction_date)`

  Account statement history           `(account_id, transaction_date DESC)`

  User import history                 `(user_id, created_at DESC)`

  Import row lookup                   `(import_job_id, row_number)` unique

  Open anomalies                      `(user_id, status, created_at DESC)`

  Active budgets                      `(user_id, is_active, start_date)`

  Forecast history                    `(user_id, generated_at DESC)`

  Pending notifications               `(user_id, status, scheduled_at)`
  --------------------------------------------------------------------------------

Avoid premature partitioning. Evaluate table size and query plans first.
If transactions grow substantially, consider date-based partitioning
only after verifying PostgreSQL constraints and query behavior.

------------------------------------------------------------------------

## 11. Canonical CSV-to-transaction contract

The ingestion layer should normalize different statement formats into
one internal representation.

Example canonical record:

``` json
{
  "transaction_date": "2026-04-12",
  "posted_at": null,
  "description_original": "UPI/P2A/123456/FOODMART",
  "description_normalized": "foodmart",
  "amount_minor": -42500,
  "currency": "INR",
  "transaction_kind": "expense",
  "payment_mode": "upi",
  "merchant_name_candidate": "Foodmart",
  "category_name_candidate": "Groceries",
  "category_confidence": 0.91,
  "source_row_number": 18
}
```

In this example, `-42500` means INR 425.00 under the INR two-decimal
minor-unit convention.

### 11.1 Input formats to support in the mock corpus

1.  Separate `Debit` and `Credit` columns.
2.  Signed `Amount` column where expenses are negative.
3.  Positive amount plus `DR`/`CR` indicator.
4.  Different date formats (`DD-MM-YYYY`, `YYYY-MM-DD`, `DD/MM/YYYY`).
5.  Variable descriptions and optional balance columns.

### 11.2 Required normalization behavior

-   Reject or flag ambiguous date formats rather than guessing silently.
-   Normalize signs consistently.
-   Preserve original description.
-   Normalize currency and reject unsupported or mixed-currency
    ambiguity.
-   Do not assume missing payment mode.
-   Mark uncertain merchant/category as unknown or low confidence.
-   Preserve source row number and import ID.
-   Keep invalid rows available for correction and explain why they
    failed.

------------------------------------------------------------------------

## 12. Synthetic mock-data specification

### 12.1 Purpose

Create a synthetic dataset large and varied enough to demonstrate every
core FinSight feature and test financial correctness. All records must
be generated; do not use real customer statements or real personal bank
data.

### 12.2 Target dataset size

Recommended starting target:

  Entity                         Target quantity
  ---------------------------- -----------------
  Synthetic users                             20
  Historical period                    12 months
  Transactions                    15,000--20,000
  Bank accounts                           25--35
  Merchants                             100--150
  System categories                       18--25
  Budgets                               100--150
  Savings goals                           20--30
  Recurring-payment patterns             60--100
  Labelled anomaly cases                200--300
  Voice evaluation prompts              100--150
  Raw CSV statement layouts                 4--5

These are generation targets, not measured product capacity limits.

### 12.3 User personas

Generate varied synthetic personas:

  ------------------------------------------------------------------------
  Persona                                      Count Behavioral
                                                     characteristics
  --------------------- ---------------------------- ---------------------
  Students                                         5 UPI-heavy, food,
                                                     transport,
                                                     subscriptions,
                                                     irregular inflows

  Young professionals                              4 Salary, rent,
                                                     commute, dining and
                                                     shopping

  Salaried                                         4 Stable income, bills,
  professionals                                      savings and
                                                     investments
                                                     represented only as
                                                     transactions if
                                                     present

  High spenders                                    3 Larger discretionary
                                                     spending and
                                                     occasional spikes

  Freelancers                                      2 Irregular income,
                                                     variable monthly cash
                                                     flow

  High savers                                      2 Lower discretionary
                                                     spend, recurring
                                                     savings contributions
  ------------------------------------------------------------------------

Personas are synthetic behavioral templates, not labels inferred about
real users.

### 12.4 Primary demo user

Create one primary demo user with approximately 500--800 transactions
over 12 months.

The primary user should include: - Salary or recurring income. -
UPI-heavy daily transactions. - Groceries and dining. - Transport and
fuel. - Shopping. - Utilities and rent. - Subscriptions and recurring
payments. - Refunds and reversals. - At least one internal account
transfer. - A visible category-spending spike. - One large but
legitimate purchase. - A few duplicate candidates. - One or more savings
goals and budgets. - Enough history for a simple forecast demonstration.

This user should make the voice queries and dashboard immediately
understandable.

### 12.5 Scenario coverage

Include explicit labelled scenarios:

1.  Normal stable monthly spending.
2.  Food/dining spending increases sharply.
3.  Large one-time purchase.
4.  Duplicate transaction candidate.
5.  Subscription price increases.
6.  Irregular salary or freelance income.
7.  Budget threshold exceeded.
8.  Savings goal falling behind schedule.
9.  Refund after a purchase.
10. Internal transfer between owned accounts.
11. Seasonal travel or festival spending.
12. Merchant alias variation.
13. Ambiguous transaction description.
14. Missing/invalid CSV fields.
15. A user with insufficient history for forecasting.

Each scenario should have a stable scenario ID and ground-truth labels.

### 12.6 Dataset components

Recommended generated files:

``` text
data/
  synthetic/
    users.csv
    bank_accounts.csv
    categories.csv
    merchants.csv
    merchant_aliases.csv
    transactions.csv
    budgets.csv
    savings_goals.csv
    recurring_payments.csv
    recurring_payment_transactions.csv
    anomaly_ground_truth.csv
    voice_eval.jsonl
    manifest.json
  raw/
    statement_format_01.csv
    statement_format_02.csv
    statement_format_03.csv
    statement_format_04.csv
    statement_format_05.csv
```

Keep raw statement fixtures distinct from canonical normalized
transaction files. The raw fixtures test ingestion; canonical files seed
deterministic database state.

### 12.7 Generator implementation

Suggested tooling: - Python. - Faker for names and merchant-like
descriptions. - NumPy for controlled random distributions. - Pandas for
output and batch transformations. - Python `random` and NumPy seeded RNG
for reproducibility.

The generator should: - Accept a seed. - Accept number of users, months
and transactions/persona. - Produce deterministic output for the same
seed/configuration. - Generate referentially consistent IDs. - Generate
transactions chronologically. - Keep account currency consistent unless
a multi-currency test is intended. - Generate ground-truth anomaly
labels separately from detector output. - Record generator version and
seed in `manifest.json`.

### 12.8 Ground truth and evaluation split

For anomaly detection: - Preserve scenario labels in
`anomaly_ground_truth.csv`. - Separate generated anomalies from the
detector's predicted anomalies. - Measure precision, recall and F1 on
labelled cases. - Include benign large purchases to test false
positives.

For forecasting: - Split chronologically, not randomly. - Example: first
9 months for training, next 3 months for holdout. - Fit preprocessing
only on the training period. - Compare against a simple baseline. - Do
not allow future transactions to influence features for earlier
forecasts.

For voice: - Each evaluation prompt should include expected intent,
normalized parameters, expected tool and expected result properties. -
Avoid hardcoding one exact natural-language transcript if paraphrases
should be supported.

Example JSONL record:

``` json
{
  "case_id": "voice_001",
  "utterance": "How much did I spend on food last month?",
  "language": "en",
  "expected_intent": "category_spending",
  "expected_parameters": {
    "category": "Food",
    "period": "previous_calendar_month"
  },
  "expected_tool": "get_category_breakdown",
  "expected_currency": "INR"
}
```

### 12.9 Data quality checks

The generator must verify: - Every account belongs to an existing
user. - Every transaction references a valid account and user. - Every
referenced category and merchant exists. - Amounts and currencies are
valid. - Dates fall within the configured generation window. - Internal
transfer pairs reconcile within a defined tolerance. - Refunds link to
plausible original purchases where generated. - Budgets and goals have
valid date ranges and positive amounts. - Anomaly ground-truth
references existing transactions. - Voice evaluation cases use valid
categories and date parameters.

------------------------------------------------------------------------

## 13. Data migration and implementation order

1.  Create users and bank accounts.
2.  Create system categories and merchant master.
3.  Create import jobs and import rows.
4.  Create canonical transactions and ownership constraints.
5.  Add budgets and savings goals.
6.  Add recurring payments and evidence links.
7.  Add anomaly and forecast tables.
8.  Add voice session and turn metadata.
9.  Add notification preferences and notifications.
10. Add Slack links and external event idempotency.
11. Add indexes after query patterns are exercised.
12. Load synthetic fixtures and run integrity checks.

Use Alembic migrations. Never modify production schema manually without
a migration.

------------------------------------------------------------------------

## 14. Schema acceptance criteria

The schema is ready for feature implementation when:

-   All user-owned records have enforceable ownership paths.
-   Transactions use exact monetary representation.
-   Import rows can be traced back to source files and row numbers.
-   Transfers and refunds are distinguishable from ordinary expenses.
-   Duplicate candidates can be reviewed without destructive
    deduplication.
-   Budgets and goals have explicit currency and period semantics.
-   Forecast and anomaly outputs retain model/detector versions.
-   Voice metadata retention is defined.
-   Slack events can be deduplicated.
-   Synthetic generation is seeded, reproducible and referentially
    valid.
-   Chronological forecast evaluation and labelled anomaly evaluation
    are possible.

**End of `data_schema.md`.**
