from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, func
from ...db.session import DbSession, get_db
from ..deps import get_current_user
from ...models.user import User
from ...models.snick import Snick
from ...models.sticker import Sticker

router = APIRouter()

@router.get("/search")
async def search(query: str = Query(min_length=1, max_length=100), limit: int = Query(default=20, ge=1, le=50),
                 current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    q = f"%{query.strip()}%"
    snicks = db.query(Snick).filter(or_(Snick.title.ilike(q), Snick.description.ilike(q), Snick.category.ilike(q))).limit(limit).all()
    stickers = db.query(Sticker).filter(Sticker.is_active.is_(True), Sticker.name.ilike(q)).limit(limit).all()
    return {
        "snicks": [{"id": s.id, "title": s.title, "description": s.description, "category": s.category, "difficulty": s.difficulty} for s in snicks],
        "stickers": [{"id": s.id, "name": s.name, "image_url": s.image_url, "category": s.category} for s in stickers]
    }

@router.get("/stickers")
async def list_stickers(category: str | None = None, current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    query = db.query(Sticker).filter(Sticker.is_active.is_(True))
    if category:
        query = query.filter(Sticker.category == category)
    return query.order_by(Sticker.sort_order, Sticker.name).all()
