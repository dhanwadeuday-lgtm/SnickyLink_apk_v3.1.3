import random
from datetime import datetime, timezone
from typing import List
from sqlalchemy.orm import Session
from ..models.snick import Snick, DailySnick, DailySnickState
from ..models.couple import CoupleStats

class PersonalizationService:
    @staticmethod
    def select_daily_snicks(db: Session, couple_id: str, date: datetime) -> List[Snick]:
        """
        Selects 5 Snicks for a couple based on their history, preferences,
        and current performance (difficulty alignment).
        """
        # 1. Get all available snicks
        all_snicks = db.query(Snick).all()
        if len(all_snicks) < 5:
            raise ValueError("Not enough snicks in the pool to assign daily missions")

        # 2. Gather History for weighting
        assigned_records = db.query(DailySnick).filter(DailySnick.couple_id == couple_id).all()

        # Recency Penalty: Map snick_id -> last_assigned_date
        recency_map = {}
        category_counts = {}
        for rec in assigned_records:
            recency_map[rec.snick_id] = rec.assigned_date
            # Get the snick to find its category
            s = db.query(Snick).filter(Snick.id == rec.snick_id).first()
            if s:
                category_counts[s.category] = category_counts.get(s.category, 0) + 1

        # Difficulty Adjustment based on completion rate
        stats = db.query(CoupleStats).filter(CoupleStats.couple_id == couple_id).first()
        completion_rate = stats.completion_rate if stats else 0.5
        target_difficulty = 1 if completion_rate < 0.4 else (2 if completion_rate < 0.8 else 3)

        # 3. Weighted Selection Pool
        pool = []
        for s in all_snicks:
            weight = 1.0

            # Recency Penalty: reduce weight if assigned in the last 7 days
            if s.id in recency_map:
                days_since = (date - recency_map[s.id]).days
                if days_since < 7:
                    weight *= 0.2
                elif days_since < 14:
                    weight *= 0.5

            # Category Balance: Weight up categories that are under-represented
            cat_count = category_counts.get(s.category, 0)
            weight *= (1.0 / (cat_count + 1)) * 5.0

            # Difficulty Alignment: Weight up the target difficulty
            if s.difficulty == target_difficulty:
                weight *= 2.0
            elif abs(s.difficulty - target_difficulty) > 1:
                weight *= 0.5

            pool.extend([s] * int(weight * 10))

        # If pool is too small due to heavy penalties, fallback to all snicks
        if len(pool) < 5:
            return random.sample(all_snicks, 5)

        return random.sample(pool, 5)
