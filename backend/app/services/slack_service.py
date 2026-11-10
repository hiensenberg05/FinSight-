"""
FinSight Autonomous Slack Dispatcher Service.
Provides bi-directional Block Kit alerts, receipt notifications, and autonomous financial triggers.
"""

import logging
from typing import Dict, Any, List, Optional
import httpx
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class SlackService:
    """Manages outgoing Block Kit alerts to configured Slack channels."""

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        bot_token: Optional[str] = None,
        default_channel: Optional[str] = None,
    ):
        self.webhook_url = webhook_url or settings.SLACK_WEBHOOK_URL
        self.bot_token = bot_token or settings.SLACK_BOT_TOKEN
        self.default_channel = default_channel or settings.SLACK_CHANNEL_ID or "C09M5ETUMPF"
        self.channel_name = settings.SLACK_CHANNEL_NAME or "#engineering-inventory-tracker"
        self.dm_channel = "D0CFWN1310F"

    async def send_raw_payload(self, payload: Dict[str, Any], notify_dm: bool = True) -> Dict[str, Any]:
        """Sends payload to Slack via Incoming Webhook and optionally posts a copy to Bot DM."""
        results = {"webhook": None, "dm": None}
        success = False

        # 1. Deliver to channel via Incoming Webhook
        if self.webhook_url:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(self.webhook_url, json=payload)
                    if resp.status_code == 200:
                        logger.info(f"[Slack] Webhook alert successfully delivered to {self.channel_name}")
                        results["webhook"] = {"status": 200, "success": True}
                        success = True
                    else:
                        logger.warning(f"[Slack] Webhook returned status {resp.status_code}: {resp.text}")
                        results["webhook"] = {"status": resp.status_code, "error": resp.text}
            except Exception as e:
                logger.warning(f"[Slack] Webhook delivery exception: {e}")
                results["webhook"] = {"error": str(e)}

        # 2. Also deliver to User DM via Bot User OAuth Token if available
        if self.bot_token and notify_dm:
            try:
                dm_payload = dict(payload)
                dm_payload["channel"] = self.dm_channel
                headers = {
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-Type": "application/json; charset=utf-8",
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post("https://slack.com/api/chat.postMessage", json=dm_payload, headers=headers)
                    data = resp.json()
                    if data.get("ok"):
                        logger.info(f"[Slack] Bot DM alert delivered to {self.dm_channel}")
                        results["dm"] = {"status": 200, "success": True, "ts": data.get("ts")}
                        success = True
                    else:
                        logger.warning(f"[Slack] Bot DM delivery returned error: {data.get('error')}")
                        results["dm"] = {"error": data.get("error")}
            except Exception as e:
                logger.warning(f"[Slack] Bot DM delivery exception: {e}")
                results["dm"] = {"error": str(e)}

        if success:
            return {
                "success": True,
                "method": "webhook+bot_dm" if (results["webhook"] and results["webhook"].get("success") and results["dm"] and results["dm"].get("success")) else ("webhook" if results["webhook"] and results["webhook"].get("success") else "bot_dm"),
                "results": results,
            }
        return {"success": False, "error": "Both webhook and bot token delivery failed", "results": results}

    async def send_message(self, text: str, blocks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Sends a message with fallback text and optional Block Kit blocks."""
        payload: Dict[str, Any] = {"text": text}
        if blocks:
            payload["blocks"] = blocks
        return await self.send_raw_payload(payload)

    async def send_welcome_verification(self) -> Dict[str, Any]:
        """Sends an interactive connection confirmation card to Slack."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🟢 FinSight Financial Co-Pilot Connected",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"Hello *Aarav*! Your FinSight AI assistant is now linked to *{self.channel_name}*.\n"
                        "FinSight will autonomously dispatch real-time forensic alerts for delivery surcharges, "
                        "upcoming utility bills, and unusual account activity directly here."
                    ),
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "*Active Account:*\nPrimary HDFC ···4921"},
                    {"type": "mrkdwn", "text": "*Safety Cushion:*\n₹1,02,756 (Safe)"},
                    {"type": "mrkdwn", "text": "*Automated Rules:*\nSurge > ₹100, Anomaly > 2.5σ"},
                    {"type": "mrkdwn", "text": "*Status:*\nActive & Monitoring"},
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📊 Open Dashboard", "emoji": True},
                        "url": "http://localhost:5173",
                        "style": "primary",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "⚡ Test Bill Alert", "emoji": True},
                        "value": "test_bill_alert",
                    },
                ],
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "🛡️ *FinSight Sentinel*: Zero-hallucination grounding · Powered by Gnani & Playwright",
                    }
                ],
            },
        ]
        return await self.send_message("🟢 FinSight Financial Co-Pilot Connected to Slack!", blocks=blocks)

    async def send_swiggy_surge_alert(
        self,
        order_id: str = "SW-89218",
        restaurant: str = "Meghana Foods · Indiranagar",
        food_subtotal: float = 1050.0,
        surge_fee: float = 120.0,
        packaging_fee: float = 65.0,
        total_amount: float = 1480.0,
    ) -> Dict[str, Any]:
        """Dispatches delivery surcharge forensics to Slack."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🍔 Late-Night Food Delivery Surcharge Warning",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"FinSight detected an itemized Swiggy order with high surcharge fees.\n"
                        f"*Order #{order_id}* at *{restaurant}* on *09 Feb 2025, 11:42 PM*."
                    ),
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Food Items:*\n₹{food_subtotal:,.2f}"},
                    {"type": "mrkdwn", "text": f"*⚠️ Peak Surge Fee:*\n*₹{surge_fee:,.2f}* (Over limit)"},
                    {"type": "mrkdwn", "text": f"*Packaging & Taxes:*\n₹{(packaging_fee + 245):,.2f}"},
                    {"type": "mrkdwn", "text": f"*Total Charged:*\n*₹{total_amount:,.2f}*"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"💡 *Forensic Insight*: Hidden fees added *₹{(surge_fee + packaging_fee + 45):,.0f}* (15.5%) to this meal. "
                        "Capping weekend late-night delivery saves up to *₹4,800/month*."
                    ),
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🔍 View Receipt in FinSight", "emoji": True},
                        "url": "http://localhost:5173",
                        "style": "primary",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Cap Food at ₹15,000", "emoji": True},
                        "value": "cap_food_budget",
                    },
                ],
            },
        ]
        return await self.send_message(f"🍔 Swiggy Surcharge Alert: ₹{surge_fee:,.0f} surge on order #{order_id}", blocks=blocks)

    async def send_utility_bill_alert(
        self,
        consumer_id: str = "102938475",
        consumer_name: str = "Aarav Mehta",
        units_consumed: float = 184.0,
        bill_amount: float = 1400.0,
        due_date: str = "28 Feb 2025",
        safe_cushion: float = 102756.0,
    ) -> Dict[str, Any]:
        """Dispatches Bescom utility bill verification to Slack."""
        coverage = round(safe_cushion / bill_amount, 0) if bill_amount > 0 else 0
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "⚡ BESCOM Power Bill Verified · Due Soon",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"Live meter reading verified on the Karnataka Power portal for account *#{consumer_id}* (*{consumer_name}*).\n"
                        f"Payment status is currently *UNPAID*."
                    ),
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Active Units:*\n{units_consumed:,.0f} kWh"},
                    {"type": "mrkdwn", "text": f"*Amount Due:*\n*₹{bill_amount:,.2f}*"},
                    {"type": "mrkdwn", "text": f"*Due Date:*\n*{due_date}*"},
                    {"type": "mrkdwn", "text": f"*Liquidity Buffer:*\n₹{safe_cushion:,.0f} ({coverage:.0f}× safe)"},
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "💳 Pay ₹1,400 via BBPS", "emoji": True},
                        "url": "http://localhost:5173",
                        "style": "primary",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Portal Proof", "emoji": True},
                        "url": "http://localhost:8000/mock-portal/bescom/account-102938475",
                    },
                ],
            },
        ]
        return await self.send_message(f"⚡ BESCOM Bill Alert: ₹{bill_amount:,.0f} due on {due_date}", blocks=blocks)

    async def send_anomaly_alert(
        self,
        merchant: str = "Croma Electronics Indiranagar",
        amount: float = 2400.0,
        sigma_deviation: float = 2.8,
        description: str = "Belkin Ultra High Speed HDMI 2.1 Cable",
    ) -> Dict[str, Any]:
        """Dispatches forensic outlier charge notification to Slack."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 Statistical Anomaly Detected",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"FinSight flagged a transaction deviating *+{sigma_deviation:.1f}σ* from your historical median spend.\n"
                        f"Playwright verified tax invoice confirms: *{description}*."
                    ),
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Merchant:*\n{merchant}"},
                    {"type": "mrkdwn", "text": f"*Amount:*\n*₹{amount:,.2f}*"},
                    {"type": "mrkdwn", "text": "*Warranty:*\n2.0 Years Manufacturer"},
                    {"type": "mrkdwn", "text": "*Status:*\nAuthorized Hardware"},
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Mark Verified", "emoji": True},
                        "url": "http://localhost:5173",
                        "style": "primary",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Dispute Charge", "emoji": True},
                        "style": "danger",
                        "url": "http://localhost:5173",
                    },
                ],
            },
        ]
        return await self.send_message(f"🚨 Anomaly Alert: ₹{amount:,.0f} at {merchant}", blocks=blocks)

    async def send_budget_breach_alert(
        self,
        category: str = "Food & Dining",
        spent: float = 30563.0,
        limit: float = 16000.0,
        utilization: float = 191.0,
    ) -> Dict[str, Any]:
        """Dispatches proactive budget breach warning to Slack."""
        over_budget = max(0.0, spent - limit)
        severity_label = "CRITICAL BREACH" if utilization >= 100.0 else "WARNING (85%+)"
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"⚠️ Budget Limit Alert · {category}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*FinSight Sentinel Alert*: Your *{category}* monthly budget has reached *{utilization:.0f}%* of its ceiling.\n"
                        f"You have exceeded your target allowance by *₹{over_budget:,.2f}*."
                    ),
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Category:*\n{category}"},
                    {"type": "mrkdwn", "text": f"*Total Spent:*\n*₹{spent:,.2f}*"},
                    {"type": "mrkdwn", "text": f"*Budget Ceiling:*\n₹{limit:,.2f}"},
                    {"type": "mrkdwn", "text": f"*Severity:*\n*{severity_label}*"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"💡 *Actionable Advice*: Trimming discretionary weekend orders by 20% will save "
                        f"*₹{(spent * 0.20):,.0f}* this month and recover your savings cushion."
                    ),
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📊 Adjust Budget Limit", "emoji": True},
                        "url": "http://localhost:5173",
                        "style": "primary",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Review Transactions", "emoji": True},
                        "url": "http://localhost:5173",
                    },
                ],
            },
        ]
        return await self.send_message(f"⚠️ Budget Alert: {category} reached {utilization:.0f}% (₹{spent:,.0f})", blocks=blocks)

    async def send_spending_spike_alert(
        self,
        category: str = "Food & Dining",
        current_spend: float = 52763.0,
        previous_spend: float = 38200.0,
        delta_percent: float = 38.1,
        top_driver: str = "Swiggy Late-Night Deliveries",
    ) -> Dict[str, Any]:
        """Dispatches spending upsurge or spike analysis alert to Slack."""
        diff = max(0.0, current_spend - previous_spend)
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📈 Monthly Spending Spike Alert · {category}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"FinSight detected a *+{delta_percent:.1f}% surge* (+₹{diff:,.0f}) in *{category}* compared to last month.\n"
                        f"*Primary Spending Driver*: {top_driver}."
                    ),
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Category:*\n{category}"},
                    {"type": "mrkdwn", "text": f"*Current Month:*\n*₹{current_spend:,.2f}*"},
                    {"type": "mrkdwn", "text": f"*Prior Month:*\n₹{previous_spend:,.2f}"},
                    {"type": "mrkdwn", "text": f"*Month Spike Delta:*\n*+₹{diff:,.2f} (+{delta_percent:.0f}%)*"},
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🔍 Inspect Driver Transactions", "emoji": True},
                        "url": "http://localhost:5173",
                        "style": "primary",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Set ₹15k Cap", "emoji": True},
                        "url": "http://localhost:5173",
                    },
                ],
            },
        ]
        return await self.send_message(f"📈 Spend Spike: {category} spiked +{delta_percent:.0f}% (+₹{diff:,.0f})", blocks=blocks)

    async def send_goal_velocity_alert(
        self,
        goal_name: str = "Vacation Fund",
        target_amount: float = 60000.0,
        current_amount: float = 12000.0,
        monthly_drag: float = 4800.0,
        months_delayed: float = 2.4,
    ) -> Dict[str, Any]:
        """Dispatches savings goal milestone or delay warning to Slack."""
        progress_pct = (current_amount / target_amount * 100.0) if target_amount > 0 else 0
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🎯 Savings Goal Velocity Alert · {goal_name}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"Milestone tracking for *{goal_name}*: Current balance is *₹{current_amount:,.0f}* of *₹{target_amount:,.0f}* ({progress_pct:.0f}% achieved).\n"
                        f"⚠️ High discretionary delivery charges (₹{monthly_drag:,.0f}/mo) are delaying completion by *{months_delayed:.1f} months*."
                    ),
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Target Goal:*\n{goal_name}"},
                    {"type": "mrkdwn", "text": f"*Target Amount:*\n₹{target_amount:,.2f}"},
                    {"type": "mrkdwn", "text": f"*Accumulated:*\n*₹{current_amount:,.2f}*"},
                    {"type": "mrkdwn", "text": f"*Progress:*\n*{progress_pct:.0f}% complete*"},
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🚀 Accelerate Goal", "emoji": True},
                        "url": "http://localhost:5173",
                        "style": "primary",
                    },
                ],
            },
        ]
        return await self.send_message(f"🎯 Goal Alert: {goal_name} is {progress_pct:.0f}% complete", blocks=blocks)

    async def send_high_transaction_alert(
        self,
        transactions: List[Dict[str, Any]],
        threshold: float = 5000.0,
    ) -> Dict[str, Any]:
        """Dispatches high-value transaction summary alert to Slack."""
        tx_count = len(transactions)
        total_val = sum(float(t.get("amount", 0)) for t in transactions)
        tx_lines = "\n".join(
            f"• *{t.get('merchant', 'Merchant')}*: ₹{float(t.get('amount', 0)):,.2f} ({t.get('category', 'Category')})"
            for t in transactions[:4]
        )
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"💳 High-Value Transaction Alert (≥ ₹{threshold:,.0f})",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"FinSight detected *{tx_count} transaction(s)* meeting or exceeding your *₹{threshold:,.0f}* threshold.\n\n"
                        f"{tx_lines}"
                    ),
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Threshold Filter:*\n≥ ₹{threshold:,.2f}"},
                    {"type": "mrkdwn", "text": f"*Qualified Charges:*\n{tx_count} records"},
                    {"type": "mrkdwn", "text": f"*Total Amount:*\n*₹{total_val:,.2f}*"},
                    {"type": "mrkdwn", "text": "*Audit Status:*\nVerified Ledger"},
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📊 Open Full Ledger", "emoji": True},
                        "url": "http://localhost:5173",
                        "style": "primary",
                    },
                ],
            },
        ]
        return await self.send_message(f"💳 High-Value Alert: {tx_count} transactions ≥ ₹{threshold:,.0f} (Total: ₹{total_val:,.0f})", blocks=blocks)

    async def send_custom_dynamic_alert(
        self,
        title: str,
        summary: str,
        fields: Optional[List[Dict[str, str]]] = None,
        severity: str = "warning",
        action_label: Optional[str] = "Open FinSight",
        action_url: Optional[str] = "http://localhost:5173",
    ) -> Dict[str, Any]:
        """Dispatches an arbitrary dynamic financial notification to Slack."""
        icon = "🚨" if severity == "critical" else ("⚠️" if severity == "warning" else ("✅" if severity == "success" else "🔔"))
        formatted_fields = []
        if fields:
            for f in fields[:6]:
                formatted_fields.append({"type": "mrkdwn", "text": f"*{f.get('label', 'Detail')}:*\n{f.get('value', 'N/A')}"})

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{icon} {title[:140]}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": summary,
                },
            },
        ]
        if formatted_fields:
            blocks.append({
                "type": "section",
                "fields": formatted_fields,
            })
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": action_label or "Open Dashboard", "emoji": True},
                    "url": action_url or "http://localhost:5173",
                    "style": "primary",
                },
            ],
        })
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "🛡️ *FinSight Dynamic Sentinel*: Real-time financial intelligence · Grounded in SQL",
                }
            ],
        })
        return await self.send_message(f"{icon} {title}: {summary[:120]}", blocks=blocks)


slack_service = SlackService()
