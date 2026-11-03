from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.controller.traffic_controller import controller

router = APIRouter(prefix="/api")


def ghi_log(db: Session, action: str, details: str, user_id: int | None = None):
    db.add(models.SystemLog(user_id=user_id, action_type=action, details=details))
    db.commit()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/cameras", response_model=list[schemas.CameraOut])
def list_cameras(db: Session = Depends(get_db)):
    return db.query(models.Camera).all()


@router.post("/cameras", response_model=schemas.CameraOut, status_code=201)
def create_camera(data: schemas.CameraIn, db: Session = Depends(get_db)):
    cam = models.Camera(**data.model_dump())
    db.add(cam); db.commit(); db.refresh(cam)
    return cam


@router.get("/status")
def get_status():
    return controller.trang_thai()


@router.post("/control/mode")
def set_mode(data: schemas.ModeIn, db: Session = Depends(get_db)):
    controller.chuyen_che_do(data.mode)
    ghi_log(db, f"SWITCH_{data.mode}", f"Chuyen che do sang {data.mode}", data.user_id)
    return controller.trang_thai()


@router.post("/control/force-phase")
def force_phase(data: schemas.ForcePhaseIn, db: Session = Depends(get_db)):
    try:
        steps = controller.ep_pha(data.direction_pair)
    except PermissionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    ghi_log(db, "OVERRIDE_GREEN", f"Ep xanh {data.direction_pair}: {steps}", data.user_id)
    return {"steps": steps, **controller.trang_thai()}


@router.get("/logs")
def list_logs(limit: int = 20, db: Session = Depends(get_db)):
    rows = db.query(models.SystemLog).order_by(models.SystemLog.id.desc()).limit(limit).all()
    return [{"id": r.id, "action": r.action_type, "details": r.details,
             "created_at": r.created_at.isoformat()} for r in rows]
