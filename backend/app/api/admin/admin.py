from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from ...db.session import get_db, DbSession
from ..deps import get_current_user
from ...models.user import User
from ...models.snick import Snick, DailySnick, SnickPillar, DailySnickState
from ...models.community import PostReport, PostReaction
from ...models.analytics import AnalyticsEvent
from ...models.events import AuditLog
from ...services.event_bus import EventBus

router = APIRouter()

# --- Admin Models ---
class SnickCreate(BaseModel):
    title: str
    description: str
    category: str
    difficulty: int
    pillar: SnickPillar
    requires_photo: bool = False

class ReportResolution(BaseModel):
    status: str # RESOLVED, REJECTED
    admin_note: Optional[str] = None

# --- Admin Logic ---

def verify_admin(current_user: User):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@router.post("/snicks", response_model=None)
async def add_snick_to_pool(
    req: SnickCreate,
    admin: User = Depends(verify_admin),
    db: DbSession = Depends(get_db)
):
    new_snick = Snick(
        title=req.title,
        description=req.description,
        category=req.category,
        difficulty=req.difficulty,
        pillar=req.pillar,
        requires_photo=req.requires_photo
    )
    db.add(new_snick)
    db.commit()
    db.add(AuditLog(actor_user_id=admin.id, action="ADMIN_SNICK_CREATED", entity_type="snick", entity_id=str(new_snick.id), metadata_json={"title": new_snick.title}))
    db.commit()
    return {"message": "Snick added to pool successfully"}

@router.get("/reports")
async def list_reports(
    admin: User = Depends(verify_admin),
    db: DbSession = Depends(get_db)
):
    reports = db.query(PostReport).filter(PostReport.status == "PENDING").all()
    return reports

@router.post("/reports/{report_id}/resolve")
async def resolve_report(
    report_id: UUID,
    req: ReportResolution,
    admin: User = Depends(verify_admin),
    db: DbSession = Depends(get_db)
):
    report = db.query(PostReport).filter(PostReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if req.status not in {"RESOLVED","REJECTED"}:
        raise HTTPException(status_code=400, detail="Status must be RESOLVED or REJECTED")
    report.status = req.status
    db.flush()
    if req.status == "RESOLVED":
        EventBus.publish(db,"REPORT_RESOLVED","community_post",str(report.post_id),
                         {"report_id":str(report.id),"admin_note":req.admin_note},str(admin.id))
    db.commit()
    db.add(AuditLog(actor_user_id=admin.id, action="ADMIN_REPORT_RESOLVED", entity_type="post_report", entity_id=str(report.id), metadata_json={"status": req.status, "admin_note": req.admin_note}))
    db.commit()
    return {"message": "Report resolved"}

@router.get("/metrics")
async def get_system_metrics(
    admin: User = Depends(verify_admin),
    db: DbSession = Depends(get_db)
):
    total_users = db.query(User).count()
    total_couples = db.query(DailySnick).filter(DailySnick.state == DailySnickState.VERIFIED).count() # Simplified

    return {
        "total_users": total_users,
        "active_couples": total_couples,
        "system_status": "Healthy"
    }

@router.get("/audit-logs")
async def audit_logs(limit: int = 100, admin: User = Depends(verify_admin), db: DbSession = Depends(get_db)):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(limit, 500)).all()
