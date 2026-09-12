import os
import redis
from typing import List, Tuple, Dict
from sqlalchemy.orm import Session
from ..models.snick import DiamondTransaction

class LeaderboardService:
    # Redis Config
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

    def __init__(self):
        self.redis = redis.StrictRedis(
            host=self.redis_host(),
            port=self.redis_port(),
            password=self.redis_password(),
            decode_responses=True
        )

    def redis_host(self): return self.REDIS_HOST
    def redis_port(self): return self.REDIS_PORT
    def redis_password(self): return self.REDIS_PASSWORD

    def update_score(self, couple_id: str, score_delta: int):
        """
        Updates the couple's score in the global leaderboard.
        """
        # Use a sorted set for the all-time leaderboard
        self.redis.zincrby("leaderboard:all_time", score_delta, couple_id)

        # Update daily leaderboard (key is date string)
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.redis.zincrby(f"leaderboard:daily:{today}", score_delta, couple_id)

    def get_rankings(self, time_frame: str = "all_time", limit: int = 10) -> List[Tuple[str, float]]:
        """
        Returns the top couples for the given timeframe.
        """
        if time_frame == "all_time":
            key = "leaderboard:all_time"
        else:
            from datetime import datetime, timezone
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            key = f"leaderboard:daily:{today}"

        # ZREVRANGE returns the highest scores first
        return self.redis.zrevrange(key, 0, limit - 1, withscores=True)

    def get_couple_rank(self, couple_id: str, time_frame: str = "all_time") -> Dict[str, any]:
        """
        Returns the rank and score for a specific couple.
        """
        if time_frame == "all_time":
            key = "leaderboard:all_time"
        else:
            from datetime import datetime, timezone
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            key = f"leaderboard:daily:{today}"

        rank = self.redis.zrevrank(key, couple_id)
        score = self.redis.zscore(key, couple_id)

        return {
            "rank": rank + 1 if rank is not None else None,
            "score": int(score) if score is not None else 0
        }

# Singleton for the app
leaderboard_service = LeaderboardService()
