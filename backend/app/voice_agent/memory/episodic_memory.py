"""
Episodic Memory Service for FinSight Voice Agent.
Persists and retrieves cross-session user decisions, commitments,
savings milestones, and contextual preferences.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.db.models import ConversationEpisode

logger = logging.getLogger(__name__)


class EpisodicMemoryService:
    """
    Manages episodic memory across independent voice and text sessions.
    """

    @classmethod
    async def record_episode(
        cls,
        db: AsyncSession,
        user_id: str,
        episode_type: str,
        topic: str,
        summary: str,
        facts: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> ConversationEpisode:
        """
        Record a significant conversational decision or financial event.
        """
        episode = ConversationEpisode(
            user_id=user_id,
            session_id=session_id,
            episode_type=episode_type,
            topic=topic,
            summary=summary,
            facts_json=json.dumps(facts or {}, ensure_ascii=False),
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(episode)
        await db.commit()
        await db.refresh(episode)
        logger.info(f"Recorded episodic memory: user={user_id}, topic={topic}, type={episode_type}")
        return episode

    @classmethod
    async def get_recent_episodes(
        cls,
        db: AsyncSession,
        user_id: str,
        limit: int = 5,
        topic: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent active episodes for a user.
        """
        stmt = (
            select(ConversationEpisode)
            .where(
                ConversationEpisode.user_id == user_id,
                ConversationEpisode.is_active.is_(True),
            )
            .order_by(desc(ConversationEpisode.created_at))
            .limit(limit)
        )
        if topic:
            stmt = stmt.where(ConversationEpisode.topic == topic)

        res = await db.execute(stmt)
        episodes = res.scalars().all()
        return [
            {
                "id": ep.id,
                "episode_type": ep.episode_type,
                "topic": ep.topic,
                "summary": ep.summary,
                "facts": json.loads(ep.facts_json) if ep.facts_json else {},
                "created_at": ep.created_at.isoformat() if ep.created_at else None,
            }
            for ep in episodes
        ]

    @classmethod
    async def retrieve_semantic_episodes(
        cls,
        db: AsyncSession,
        user_id: str,
        query: str,
        limit: int = 3,
        threshold: float = 0.04,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves active episodes and ranks them via vector embeddings
        and cosine similarity against the user query.
        """
        from backend.app.voice_agent.memory.semantic_retriever import semantic_memory_retriever

        all_active = await cls.get_recent_episodes(db, user_id, limit=20)
        if not all_active:
            return []

        ranked_results = semantic_memory_retriever.rank_episodes(
            query=query,
            episodes=all_active,
            top_k=limit,
            threshold=threshold,
        )
        return [ep for ep, score in ranked_results]

    @classmethod
    async def ensure_baseline_episodes(cls, db: AsyncSession, user_id: str):
        """
        Seed baseline episodic memories if none exist for Aarav Mehta.
        """
        existing = await cls.get_recent_episodes(db, user_id, limit=1)
        if existing:
            return

        baselines = [
            (
                "budget_commitment",
                "food_dining_budget",
                "Aarav confirmed setting a strict ₹16,000 monthly budget cap on Food & Dining to curb weekend Swiggy and Zomato surges.",
                {"category": "Food & Dining", "amount": 16000.0, "status": "active"},
            ),
            (
                "goal_milestone",
                "vacation_fund_goal",
                "Aarav targeted reaching a ₹60,000 Vacation Fund by allocating ₹5,200 monthly discretionary savings, aiming for completion by April 2027.",
                {"goal_name": "Vacation Fund", "target_amount": 60000.0, "monthly_contribution": 5200.0, "target_date": "2027-04-30"},
            ),
            (
                "spending_preference",
                "croma_electronics_outlier",
                "Aarav clarified the ₹2,400 Croma Retail purchase on Feb 12 was a verified, one-off electronic accessory, not recurring spend.",
                {"merchant": "Croma Retail", "amount": 2400.0, "is_verified": True},
            ),
        ]

        for ep_type, topic, summary, facts in baselines:
            await cls.record_episode(db, user_id, ep_type, topic, summary, facts)
