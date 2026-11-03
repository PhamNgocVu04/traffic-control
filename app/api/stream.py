from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.vision.engine import VisionEngine

router = APIRouter(prefix="/api")
engine = VisionEngine()


@router.get("/stream/{direction}")
def stream_camera(direction: str, db: Session = Depends(get_db)):
    """Phat video cua camera theo huong (North/South/East/West) duoi dang MJPEG."""
    cam = db.query(models.Camera).filter(models.Camera.direction == direction).first()
    if cam is None:
        raise HTTPException(status_code=404, detail=f"Khong co camera huong {direction}")
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
