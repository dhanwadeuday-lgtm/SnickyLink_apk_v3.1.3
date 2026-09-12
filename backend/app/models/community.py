from sqlalchemy import Column, String, UUID, ForeignKey, Enum, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from .base import Base, TimestampMixin
import uuid
import enum

class PostVisibility(enum.Enum):
    PRIVATE_COUPLE = "private_couple"
    COMMUNITY = "community"

class CommunityPost(Base, TimestampMixin):
    __tablename__ = "community_posts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    couple_id = Column(PGUUID(as_uuid=True), ForeignKey("couples.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    media_id = Column(PGUUID(as_uuid=True), ForeignKey("media.id"), nullable=True)
    visibility = Column(Enum(PostVisibility), default=PostVisibility.PRIVATE_COUPLE, nullable=False, index=True)
    moderation_status = Column(String, nullable=False, default="PENDING", index=True)
    moderation_reason = Column(String, nullable=True)

class PostReaction(Base):
    __tablename__ = "post_reactions"

    post_id = Column(PGUUID(as_uuid=True), ForeignKey("community_posts.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    reaction_type = Column(String, nullable=False) # e.g., "heart", "fire", "clap"

class PostReport(Base, TimestampMixin):
    __tablename__ = "post_reports"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    post_id = Column(PGUUID(as_uuid=True), ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False)
    reason = Column(String, nullable=False)
    status = Column(String, default="PENDING") # PENDING, RESOLVED, REJECTED

class UserBlock(Base, TimestampMixin):
    __tablename__ = "user_blocks"

    blocker_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    blocked_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
