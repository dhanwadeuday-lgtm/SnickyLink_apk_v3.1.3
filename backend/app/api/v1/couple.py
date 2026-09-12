from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone
import uuid
from jose import jwt

from ...db.session import get_db, DbSession
from ...models.user import User
from ...models.couple import Couple, CoupleMember
from ...models.invite import Invite
from ..deps import get_current_user, get_current_couple_id, get_current_active_user
from ..core.security import SECRET_KEY, ALGORITHM
from ...services.analytics_service import AnalyticsService

router = APIRouter()

class InviteResponse(BaseModel):
    token: str
    invite_link: str

class PairRequest(BaseModel):
    token: str

@router.post("/invites/generate", response_model=InviteResponse)
async def generate_invite(
    current_user: User = Depends(get_current_active_user),
    db: DbSession = Depends(get_db)
):
    # Check if user is already paired
    membership = db.query(CoupleMember).filter(CoupleMember.user_id == current_user.id).first()
    if membership:
        raise HTTPException(status_code=400, detail="User is already paired")

    # Create signed JWT token
    expires = datetime.now(timezone.utc) + timedelta(hours=48)
    payload = {
        "sub": str(current_user.id),
        "exp": expires,
        "type": "pairing_invite"
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # Store invite in DB
    invite = Invite(
        inviter_id=current_user.id,
        token=token,
        expires_at=expires
    )
    db.add(invite)
    db.commit()

    invite_link = f"https://snickylink.app/pair?token={token}"
    return InviteResponse(token=token, invite_link=invite_link)

@router.post("/pair")
async def pair_partners(
    pair_req: PairRequest,
    current_user: User = Depends(get_current_active_user),
    db: DbSession = Depends(get_db)
):
    # 1. Validate Token
    try:
        payload = jwt.decode(pair_req.token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "pairing_invite":
            raise HTTPException(status_code=400, detail="Invalid token type")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    inviter_id = payload.get("sub")

    # 2. Check DB for invite validity
    invite = db.query(Invite).filter(Invite.token == pair_req.token, Invite.used_at == None).first()
    if not invite:
        raise HTTPException(status_code=400, detail="Invite is invalid or already used")

    if invite.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invite has expired")

    # 3. Check eligibility
    # Check Partner A (inviter)
    inviter_membership = db.query(CoupleMember).filter(CoupleMember.user_id == inviter_id).first()
    if inviter_membership:
        raise HTTPException(status_code=400, detail="Inviter is already paired")

    # Check Partner B (current_user)
    partner_membership = db.query(CoupleMember).filter(CoupleMember.user_id == current_user.id).first()
    if partner_membership:
        raise HTTPException(status_code=400, detail="You are already paired")

    # 4. Atomic Pairing Transaction
    try:
        new_couple = Couple()
        db.add(new_couple)
        db.flush() # Get couple_id

        # Link Partner A
        db.add(CoupleMember(user_id=inviter_id, couple_id=new_couple.id))
        # Link Partner B
        db.add(CoupleMember(user_id=current_user.id, couple_id=new_couple.id))

        # Mark invite as used
        invite.used_at = datetime.now(timezone.utc)

        # Log Analytics Event
        AnalyticsService.log_event(
            db=db,
            event_name="couple_paired",
            couple_id=str(new_couple.id),
            user_id=str(current_user.id),
            properties={"inviter_id": inviter_id}
        )

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Pairing failed: {str(e)}")

    return {"message": "Successfully paired!"}

@router.get("/me/couple")
async def get_my_couple(
    couple_id: str = Depends(get_current_couple_id),
    db: DbSession = Depends(get_db)
):
    # This route proves the middleware works
    return {"couple_id": couple_id}
