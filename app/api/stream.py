import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.vision.engine import VisionEngine, STREAM_FPS
from app.vision.worker import manager

router = APIRouter(prefix="/api")
engine = VisionEngine()


@router.get("/stream/{direction}")
def stream_camera(direction: str, db: Session = Depends(get_db)):
    """Phat video cua camera (North/South/East/West) duoi dang MJPEG.
    Co worker: phat khung hinh da ve khung xe. Khong co worker: phat video tho."""
    cam = db.query(models.Camera).filter(models.Camera.direction == direction).first()
    if cam is None:
        raise HTTPException(status_code=404, detail=f"Khong co camera huong {direction}")

    worker = manager.get(direction)
    if worker is not None:
        if worker.error:
            raise HTTPException(status_code=503, detail=worker.error)

        def from_worker():
            while worker.is_alive():
                jpg = worker.lay_khung_hinh()
                if jpg:
                    yield engine.dong_goi_mjpeg(jpg)
                time.sleep(1 / STREAM_FPS)

        return StreamingResponse(from_worker(), media_type="multipart/x-mixed-replace; boundary=frame")

    try:
        frames = engine.mjpeg_stream(cam.stream_url)
        next_frame = next(frames)  # thu doc 1 khung de bao loi som neu video hong/thieu
    except (FileNotFoundError, StopIteration):
        cam.status = "error"; db.commit()
        raise HTTPException(status_code=503, detail=f"Khong doc duoc video: {cam.stream_url}")

    def body():
        yield next_frame
        yield from frames

    return StreamingResponse(body(), media_type="multipart/x-mixed-replace; boundary=frame")


@router.get("/counts")
def get_counts():
    """So xe moi nhat cua tung huong: {"North": {"car": 5, ..., "total": 8, "density": 9.5}, ...}"""
    return {d: w.lay_so_xe() for d, w in manager.workers.items()}


class RoiIn(BaseModel):
    polygon: list[tuple[float, float]] | None  # cac dinh da giac, toa do ti le 0..1; None = toan khung


@router.put("/cameras/{direction}/roi")
def set_roi(direction: str, data: RoiIn, db: Session = Depends(get_db)):
    """Cau hinh vung ROI (vung lan duong de dem xe) cho 1 camera."""
    cam = db.query(models.Camera).filter(models.Camera.direction == direction).first()
    if cam is None:
        raise HTTPException(status_code=404, detail=f"Khong co camera huong {direction}")
    if data.polygon is not None and (len(data.polygon) < 3 or
                                     not all(0 <= x <= 1 and 0 <= y <= 1 for x, y in data.polygon)):
        raise HTTPException(status_code=422, detail="ROI can >= 3 diem, toa do trong khoang 0..1")
    cam.roi_config = {"polygon": data.polygon} if data.polygon else None
    db.commit()
    worker = manager.get(direction)
    if worker is not None:
        worker.roi = data.polygon  # cap nhat ngay, khong can khoi dong lai
    return {"direction": direction, "roi": cam.roi_config}
