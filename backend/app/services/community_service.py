import os
import json
import redis
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.community import CommunityPost, PostVisibility, PostReaction, PostReport, UserBlock
from ..models.user import User

class CommunityService:
    # Redis Config for Caching
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

    def __init__(self):
        self.redis = redis.StrictRedis(
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
            password=self.REDIS_PASSWORD,
            decode_responses=True
        )

    @staticmethod
    def create_post(db: Session, couple_id: str, creator_id: str, content: str, media_id: Optional[str] = None, visibility: PostVisibility = PostVisibility.PRIVATE_COUPLE):
        post = CommunityPost(
            couple_id=couple_id,
            creator_id=creator_id,
            content=content,
            media_id=media_id,
            visibility=visibility
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        return post

    def get_community_feed(self, db: Session, current_user_id: str, limit: int = 20, offset: int = 0) -> List[CommunityPost]:
        """
        Returns posts visible to the current user, utilizing a simple Redis cache for the global public feed.
        """
        # 1. Check cache for public posts (Simplified: global cache for the first page)
        if offset == 0:
            cache_key = "community_feed:global:p1"
            cached_data = self.redis.get(cache_key)
            if cached_data:
                # We still need to filter out blocked users, so we get the IDs from cache
                # and then verify them. For simplicity in MVP, we'll use cache as a hint
                # or just bypass it for the final filtered result.
                pass

        # 2. Full logic (Same as before, but refined)
        blocked_by_me = db.query(UserBlock.blocked_id).filter(UserBlock.blocker_id == current_user_id).all()
        blocked_me = db.query(UserBlock.blocker_id).filter(UserBlock.blocked_id == current_user_id).all()
        all_blocked_ids = {id[0] for id in blocked_by_me} | {id[0] for id in blocked_me}

        from ..models.couple import CoupleMember
        membership = db.query(CoupleMember).filter(CoupleMember.user_id == current_user_id).first()
        user_couple_id = membership.couple_id if membership else None

        query = db.query(CommunityPost).filter(
            ((CommunityPost.visibility == PostVisibility.COMMUNITY) & (CommunityPost.moderation_status == "APPROVED")) |
            ((CommunityPost.visibility == PostVisibility.PRIVATE_COUPLE) & (CommunityPost.couple_id == user_couple_id))
        )

        posts = query.order_by(CommunityPost.created_at.desc()).offset(offset).limit(limit).all()
        return [p for p in posts if p.creator_id not in all_blocked_ids]

    @staticmethod
    def add_reaction(db: Session, post_id: str, user_id: str, reaction_type: str):
        reaction = PostReaction(post_id=post_id, user_id=user_id, reaction_type=reaction_type)
        db.merge(reaction) # Use merge to handle existing reactions (upsert)
        db.commit()

    @staticmethod
    def report_post(db: Session, reporter_id: str, post_id: str, reason: str):
        report = PostReport(reporter_id=reporter_id, post_id=post_id, reason=reason)
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def block_user(db: Session, blocker_id: str, blocked_id: str):
        block = UserBlock(blocker_id=blocker_id, blocked_id=blocked_id)
        db.add(block)
        db.commit()
