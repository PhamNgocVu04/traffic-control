"""Tao san 4 camera (4 huong) khi CSDL con trong."""
from app.database import SessionLocal
from app import models

DEFAULT_CAMERAS = [
    ("Cam_Huong_Bac", "North", "data/videos/north.mp4"),
    ("Cam_Huong_Nam", "South", "data/videos/south.mp4"),
    ("Cam_Huong_Dong", "East", "data/videos/east.mp4"),
    ("Cam_Huong_Tay", "West", "data/videos/west.mp4"),
]


def seed_cameras():
    """Huong nao chua co camera thi them camera mac dinh cho huong do."""
    db = SessionLocal()
    try:
        for name, direction, url in DEFAULT_CAMERAS:
            exists = db.query(models.Camera).filter(models.Camera.direction == direction).first()
            if exists is None:
                db.add(models.Camera(name=name, direction=direction, stream_url=url))
        db.commit()
    finally:
        db.close()
