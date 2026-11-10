"""
Financial Tool Definitions and JSON Schemas for FinSight ReAct Agent.
Specifies input schemas, output structures, and usage policies for the 11 deterministic tools.
"""

from typing import List, Dict, Any

TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "get_spending_summary",
        "description": "Calculates high-level income, expenses, net savings, current available bank balance, and financial health score for the current or specified period.",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "Time period to query. Examples: 'current_month', 'last_month', '2025-02', 'all'. Defaults to 'current_month'.",
                    "default": "current_month",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_category_breakdown",
        "description": "Groups user expenses by category, calculating total spent, percentage share, transaction count, and sub-merchant details for a specific category.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Optional specific category to drill into, e.g. 'Food & Dining', 'Shopping', 'Transportation'.",
                },
                "period": {
                    "type": "string",
                    "description": "Time period: 'current_month', 'last_month', '2025-02'. Defaults to 'current_month'.",
                    "default": "current_month",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of categories to return.",
                    "default": 8,
                },
            },
            "required": [],
        },
    },
    {
        "name": "compare_periods",
        "description": "Compares spending between two periods (e.g. current month vs prior month, or Feb vs Jan) to explain spending spikes, calculating rupee delta, percentage increase, and the top category drivers causing the spike.",
        "parameters": {
            "type": "object",
            "properties": {
                "period_1": {
                    "type": "string",
                    "description": "The target/newer period, e.g. 'current_month', 'Feb 2025'.",
                    "default": "current_month",
                },
                "period_2": {
                    "type": "string",
                    "description": "The baseline/prior period to compare against, e.g. 'previous_month', 'Jan 2025'.",
                    "default": "previous_month",
                },
                "lookback_days": {
                    "type": "integer",
                    "description": "Comparison lookback window in days.",
                    "default": 30,
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_top_merchants",
        "description": "Ranks counterparty merchants by total debit spend and transaction count, optionally filtered by category or payment mode.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Filter by category name, e.g. 'Food & Dining', 'Shopping', 'Transportation'.",
                },
                "payment_mode": {
                    "type": "string",
                    "description": "Filter by payment mode: 'UPI', 'Card', 'NetBanking'.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of top merchants to return.",
                    "default": 5,
                },
                "period": {
                    "type": "string",
                    "description": "Period to query.",
                    "default": "current_month",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_payment_mode_summary",
        "description": "Aggregates transactions grouped by payment mode (UPI, Card, NetBanking) with volumes, percentages, and top merchants for that mode.",
        "parameters": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "description": "Payment mode to analyze, e.g. 'UPI', 'Card', 'NetBanking'. If omitted, returns all modes.",
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter, e.g. 'Food & Dining'.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max merchants to return.",
                    "default": 5,
                },
                "period": {
                    "type": "string",
                    "description": "Period to query, such as current_month, previous_month, or YYYY-MM.",
                    "default": "current_month",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_recurring_payments",
        "description": "Retrieves upcoming recurring obligations, bills, and subscriptions due in the next N days, along with autopay status and safety checks against current cash balance.",
        "parameters": {
            "type": "object",
            "properties": {
                "days_ahead": {
                    "type": "integer",
                    "description": "Number of days ahead to look for due bills.",
                    "default": 30,
                },
                "status": {
                    "type": "string",
                    "description": "Optional status filter: 'due_soon', 'scheduled', 'paid'.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_savings_ratio",
        "description": "Calculates the user's monthly savings ratio (net savings divided by total income) and compares it against financial health benchmarks (target >= 20%).",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "Period to evaluate.",
                    "default": "current_month",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_budget_status",
        "description": "Evaluates budget limits, actual monthly spend from ledger transactions, remaining balance, and utilization percentage across active categories.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Optional specific category to check budget for, e.g. 'Food & Dining', 'Shopping'.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_forecast",
        "description": "Generates predictive cash-flow trajectory for the next 1-3 months using Holt-Winters Double Exponential Smoothing with 80% confidence interval bands.",
        "parameters": {
            "type": "object",
            "properties": {
                "months_ahead": {
                    "type": "integer",
                    "description": "Number of future months to project (1 to 6).",
                    "default": 3,
                }
            },
            "required": [],
        },
    },
    {
        "name": "find_unusual_transactions",
        "description": "Checks transactions from a recent lookback window against configured category review thresholds and existing anomaly flags.",
        "parameters": {
            "type": "object",
            "properties": {
                "lookback_days": {
                    "type": "integer",
                    "description": "Days of transaction history to scan.",
                    "default": 60,
                },
                "focus": {
                    "type": "string",
                    "description": "Specific merchant or anomaly to focus on, e.g. 'croma', 'swiggy'.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "simulate_savings_goal",
        "description": "Simulates savings goal timeline acceleration by calculating discretionary spending cuts (Food Delivery, Shopping, Entertainment) and projecting the milestone date.",
        "parameters": {
            "type": "object",
            "properties": {
                "goal_name": {
                    "type": "string",
                    "description": "Name of the target savings goal, e.g. 'Vacation Fund', 'Emergency Fund'.",
                    "default": "Vacation Fund",
                },
                "discretionary_reduction_pct": {
                    "type": "number",
                    "description": "Percentage reduction in discretionary spending (e.g. 20.0 for 20%).",
                    "default": 20.0,
                },
            },
            "required": [],
        },
    },
    {
        "name": "prepare_set_budget",
        "description": "Action Operator Tool: Prepares a proposal to set or modify a category monthly budget cap (e.g. ₹15,000 for Food & Dining). Generates a 5-minute safety confirmation card.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Category name, e.g. 'Food & Dining', 'Shopping'.",
                    "default": "Food & Dining",
                },
                "amount": {
                    "type": "number",
                    "description": "Monthly budget limit in Rupees, e.g. 15000.0",
                    "default": 15000.0,
                },
            },
            "required": ["category", "amount"],
        },
    },
    {
        "name": "prepare_create_goal",
        "description": "Action Operator Tool: Prepares a proposal to create a new savings goal (e.g. ₹60,000 for Vacation Fund). Generates a 5-minute safety confirmation card.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Goal name, e.g. 'Vacation Fund', 'Emergency Fund'.",
                    "default": "Vacation Fund",
                },
                "target_amount": {
                    "type": "number",
                    "description": "Target amount in Rupees, e.g. 60000.0",
                    "default": 60000.0,
                },
                "target_date": {
                    "type": "string",
                    "description": "Target completion date (YYYY-MM-DD), e.g. '2027-06-30'.",
                    "default": "2027-06-30",
                },
            },
            "required": ["name", "target_amount"],
        },
    },
    {
        "name": "simulate_spending_reduction",
        "description": "Predictive Advisory Tool: Interactive what-if simulation calculating monthly savings, annualized savings, and goal velocity from cutting discretionary spending.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Discretionary category to reduce, e.g. 'Food & Dining'.",
                    "default": "Food & Dining",
                },
                "reduction_pct": {
                    "type": "number",
                    "description": "Percentage reduction (0 to 50%).",
                    "default": 20.0,
                },
                "goal_name": {
                    "type": "string",
                    "description": "Target goal to accelerate.",
                    "default": "Vacation Fund",
                },
            },
            "required": [],
        },
    },
    {
        "name": "fetch_portal_receipt_forensics",
        "description": "Autonomous Browser Automation Tool: Launches a Playwright session to inspect order receipts (Swiggy, Croma), extracting line-item dishes, peak delivery surge fees, packaging costs, and full digital invoice proof.",
        "parameters": {
            "type": "object",
            "properties": {
                "merchant": {
                    "type": "string",
                    "description": "Merchant portal name ('Swiggy', 'Croma'). Defaults to 'Swiggy'.",
                    "default": "Swiggy",
                },
                "order_id": {
                    "type": "string",
                    "description": "Target order reference id.",
                    "default": "order-89218",
                },
            },
            "required": [],
        },
    },
    {
        "name": "verify_utility_portal_bill",
        "description": "Autonomous Browser Automation Tool: Launches a Playwright session on utility provider portals (BESCOM electricity) to verify active meter reading, units consumed, generated bill amount, and official due date.",
        "parameters": {
            "type": "object",
            "properties": {
                "utility_type": {
                    "type": "string",
                    "description": "Utility type ('electricity', 'bescom'). Defaults to 'electricity'.",
                    "default": "electricity",
                },
                "consumer_id": {
                    "type": "string",
                    "description": "Consumer account ID to query.",
                    "default": "102938475",
                },
            },
            "required": [],
        },
    },
    {
        "name": "dispatch_slack_alert",
        "description": "Autonomous Notification Tool: Dispatches interactive Block Kit financial alert cards to configured Slack channels (#engineering-inventory-tracker) for late-night delivery surcharges, upcoming utility bills, or 3-sigma anomalies.",
        "parameters": {
            "type": "object",
            "properties": {
                "alert_type": {
                    "type": "string",
                    "description": "Type of alert ('test', 'swiggy_surge', 'bescom_bill', 'croma_anomaly', 'digest'). Defaults to 'test'.",
                    "default": "test",
                },
                "channel": {
                    "type": "string",
                    "description": "Target Slack channel name or ID. Defaults to '#engineering-inventory-tracker'.",
                    "default": "#engineering-inventory-tracker",
                },
            },
            "required": [],
        },
    },
]
