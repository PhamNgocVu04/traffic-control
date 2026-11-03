import cv2
import numpy as np
import pytest

from app.database import SessionLocal
from app import models
from app.vision.engine import VisionEngine, roi_sang_pixel
from app.vision.worker import CameraWorker


class FakeDetector:
    """Gia lap YOLO: luon thay 2 o to + 1 xe may + 1 xe tai o vi tri co dinh (khong can cai YOLO)."""
    def detect(self, frame):
        return [
            {"cls": "car", "box": (10, 10, 60, 50), "conf": 0.9},          # goc trai tren
            {"cls": "car", "box": (300, 200, 360, 260), "conf": 0.8},      # giua
            {"cls": "motorbike", "box": (320, 220, 340, 250), "conf": 0.7},
            {"cls": "truck", "box": (500, 300, 600, 350), "conf": 0.9},    # goc phai duoi
        ]


@pytest.fixture
def video(tmp_path):
    path = str(tmp_path / "fake.avi")
    out = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 10, (640, 360))
    for _ in range(6):
        out.write(np.zeros((360, 640, 3), dtype=np.uint8))
    out.release()
    return path


def test_dem_toan_khung():
    c = VisionEngine.dem_xe(FakeDetector().detect(None))
    assert c["total"] == 4 and c["car"] == 2 and c["truck"] == 1
    assert c["density"] == 2 * 1.0 + 0.3 + 2.5      # quy doi xe con tuong duong


def test_dem_trong_roi():
    roi = roi_sang_pixel([(0.4, 0.4), (0.7, 0.4), (0.7, 0.9), (0.4, 0.9)], 640, 360)  # vung giua
    c = VisionEngine.dem_xe(FakeDetector().detect(None), roi)
    assert c["total"] == 2 and c["car"] == 1 and c["motorbike"] == 1   # chi xe o giua duoc dem


def test_ve_ket_qua_khong_doi_kich_thuoc():
    frame = np.zeros((360, 640, 3), dtype=np.uint8)
    img = VisionEngine.ve_ket_qua(frame, FakeDetector().detect(frame), None, {"total": 4, "density": 4.8})
    assert img.shape == frame.shape and img.any()     # co ve len anh


def test_worker_dem_va_luu_csdl(video):
    db = SessionLocal()
    cam = db.query(models.Camera).filter(models.Camera.direction == "North").first()
    before = db.query(models.TrafficCount).count()
    w = CameraWorker(cam.id, "North", video, None, VisionEngine(FakeDetector()),
                     detect_every=1, save_seconds=0, max_frames=3, realtime=False)
    w.run()                                           # chay dong bo trong test
    assert w.lay_so_xe()["total"] == 4
    assert w.lay_khung_hinh().startswith(b"\xff\xd8")  # la anh JPEG
    assert db.query(models.TrafficCount).count() > before
    db.close()


def test_worker_bao_loi_khi_thieu_video():
    w = CameraWorker(1, "North", "khong_co.mp4", None, VisionEngine(FakeDetector()), realtime=False)
    w.run()
    assert w.error is not None
