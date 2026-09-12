import hashlib
import os
import secrets
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from ...db.session import DbSession, get_db
from ...models.user import User
from ...models.device import UserDevice
from ...models.password_reset import PasswordResetToken
from ...core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token
from ..deps import get_current_user
from ...services.analytics_service import AnalyticsService

router = APIRouter()

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    device_token: Optional[str] = None
    platform: str = "unknown"

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)

class UserOut(BaseModel):
    id: str
    email: EmailStr
    class Config:
        from_attributes = True


def _send_reset_email(email: str, token: str):
    host = os.getenv("SMTP_HOST")
    if not host:
        return False
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM", username or "no-reply@snickylink.app")
    frontend = os.getenv("PASSWORD_RESET_URL", "https://snickylink.app/reset-password")
    msg = EmailMessage()
    msg["Subject"] = "Reset your SnickyLink password"
    msg["From"] = sender
    msg["To"] = email
    msg.set_content(f"Reset your password: {frontend}?token={token}\nThis link expires in 30 minutes.")
    with smtplib.SMTP(host, port, timeout=15) as smtp:
        if os.getenv("SMTP_TLS", "true").lower() == "true":
            smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(msg)
    return True

@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(user_in: UserCreate, db: DbSession = Depends(get_db)):
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=user_in.email, hashed_password=get_password_hash(user_in.password))
    db.add(user); db.flush()
    AnalyticsService.log_event(db=db, event_name="user_signup", user_id=str(user.id))
    db.commit(); db.refresh(user)
    return user

@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: DbSession = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if user.suspended:
        raise HTTPException(status_code=403, detail="Account suspended")
    if user_in.device_token:
        device = db.query(UserDevice).filter(UserDevice.device_token == user_in.device_token).first()
        if device:
            device.user_id = user.id; device.platform = user_in.platform; device.is_active = True
        else:
            db.add(UserDevice(user_id=user.id, device_token=user_in.device_token, platform=user_in.platform))
    db.commit()
    return Token(access_token=create_access_token({"sub": str(user.id)}),
                 refresh_token=create_refresh_token({"sub": str(user.id)}))

@router.post("/refresh", response_model=Token)
async def refresh(req: RefreshRequest, db: DbSession = Depends(get_db)):
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh" or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or user.suspended:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return Token(access_token=create_access_token({"sub": str(user.id)}),
                 refresh_token=create_refresh_token({"sub": str(user.id)}))

@router.post("/password/forgot")
async def forgot_password(req: PasswordResetRequest, db: DbSession = Depends(get_db)):
    # Always return the same response to prevent account enumeration.
    user = db.query(User).filter(User.email == req.email).first()
    if user:
        db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id,
                                             PasswordResetToken.used_at.is_(None)).update({"used_at": datetime.now(timezone.utc)})
        raw = secrets.token_urlsafe(32)
        record = PasswordResetToken(user_id=user.id,
                                    token_hash=hashlib.sha256(raw.encode()).hexdigest(),
                                    expires_at=datetime.now(timezone.utc) + timedelta(minutes=30))
        db.add(record); db.commit()
        try:
            _send_reset_email(user.email, raw)
        except Exception:
            # Do not expose mail delivery failures to callers.
            pass
    return {"message": "If an account exists for that email, a reset link has been sent."}

@router.post("/password/reset")
async def reset_password(req: PasswordResetConfirm, db: DbSession = Depends(get_db)):
    token_hash = hashlib.sha256(req.token.encode()).hexdigest()
    record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used_at.is_(None),
        PasswordResetToken.expires_at > datetime.now(timezone.utc),
    ).first()
    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    user = db.query(User).filter(User.id == record.user_id).one()
    user.hashed_password = get_password_hash(req.new_password)
    record.used_at = datetime.now(timezone.utc)
    db.query(UserDevice).filter(UserDevice.user_id == user.id).update({"is_active": False}, synchronize_session=False)
    db.commit()
    return {"message": "Password reset successfully"}

@router.delete("/logout")
async def logout(device_token: Optional[str] = None, current_user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    q = db.query(UserDevice).filter(UserDevice.user_id == current_user.id, UserDevice.is_active.is_(True))
    if device_token: q = q.filter(UserDevice.device_token == device_token)
    q.update({"is_active": False}, synchronize_session=False); db.commit()
    return {"status": "logged_out"}

@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
