import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1 import auth, couple, snicks, chat, memories, engagement, community, notifications, analytics, media, discovery
from .api.admin import admin
from .db.session import engine
from .models.base import Base
from .models import user, couple as couple_model, invite, snick, chat as chat_model, chat_keys, media as media_model, memory, calendar, community as community_model, notification, analytics as analytics_model, events, device, sticker, gamification, password_reset
from .core.scheduler import start_scheduler
from .services.event_handlers import register_event_handlers

ENV = os.getenv("APP_ENV", "development").lower()
if ENV == "production":
    if not os.getenv("SECRET_KEY") or len(os.getenv("SECRET_KEY", "")) < 32:
        raise RuntimeError("SECRET_KEY must be a strong 32+ character value in production")
    if os.getenv("AI_PROVIDER", "vision") != "mock" and not os.getenv("AI_API_KEY"):
        raise RuntimeError("AI_API_KEY must be configured for the production AI provider")
    if not os.getenv("MEDIA_SIGNING_KEY") or len(os.getenv("MEDIA_SIGNING_KEY", "")) < 32:
        raise RuntimeError("MEDIA_SIGNING_KEY must be a strong 32+ character value in production")
    if os.getenv("DATABASE_URL", "").startswith("postgresql://user:password"):
        raise RuntimeError("DATABASE_URL is still using the development placeholder")

# Development fallback; production should run migrations instead.
if os.getenv("AUTO_CREATE_TABLES", "false").lower() == "true":
    Base.metadata.create_all(bind=engine)

register_event_handlers()
if os.getenv("RUN_SCHEDULER", "true").lower() == "true":
    scheduler = start_scheduler()
else:
    scheduler = None

app = FastAPI(title="SnickyLink API", version="1.1.0")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

for router, prefix, tags in [
    (auth.router,"/auth",["Authentication"]),(couple.router,"/couple",["Couple Management"]),
    (snicks.router,"/snicks",["Daily Snicks"]),(chat.router,"/chat",["Private Chat"]),
    (memories.router,"/memories",["Couple Memories"]),(engagement.router,"/engagement",["Engagement & Rankings"]),
    (community.router,"/community",["Community Feed"]),(notifications.router,"/notifications",["Notifications"]),
    (analytics.router,"/analytics",["Couple Analytics"]),(media.router,"/media",["Media"]),
    (discovery.router,"/discovery",["Search & Discovery"]),(admin.router,"/admin",["Internal Admin Tool"]),
]: app.include_router(router, prefix=prefix, tags=tags)

@app.get("/")
async def root(): return {"message":"SnickyLink API","version":"1.1.0"}

@app.get("/health")
async def health(): return {"status":"ok"}
