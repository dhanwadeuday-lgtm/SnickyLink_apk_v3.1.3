from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ..db.session import DbSession, get_db
from ..models.user import User
from ..core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: DbSession = Depends(get_db)) -> User:
    payload = decode_token(token)
    if not payload or "sub" not in payload or payload.get("type", "access") != "access":
        raise HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found", headers={"WWW-Authenticate": "Bearer"})
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.suspended:
        raise HTTPException(status_code=403, detail="Account suspended")
    return current_user

async def get_current_couple_id(current_user: User = Depends(get_current_active_user), db: DbSession = Depends(get_db)):
    from ..models.couple import CoupleMember
    membership = db.query(CoupleMember).filter(CoupleMember.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="You must be paired with a partner to access this feature.")
    return membership.couple_id
