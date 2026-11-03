"""CameraWorker: moi camera 1 luong chay nen, doc video -> nhan dien -> dem xe -> luu CSDL.
Dashboard chi lay khung hinh moi nhat tu worker, nen nhieu nguoi xem cung khong ton them CPU."""
import threading
import time

from app import models
from app.config import DETECT_EVERY_N_FRAMES, SAVE_COUNT_SECONDS
from app.database import SessionLocal
from app.vision.engine import VisionEngine, STREAM_FPS, roi_sang_pixel, tao_detector


class CameraWorker(threading.Thread):
    def __init__(self, camera_id: int, direction: str, stream_url: str, roi, engine: VisionEngine,
                 detect_every: int = DETECT_EVERY_N_FRAMES, save_seconds: float = SAVE_COUNT_SECONDS,
                 max_frames: int | None = None, realtime: bool = True):
        super().__init__(daemon=True, name=f"cam-{direction}")
        self.camera_id, self.direction, self.stream_url = camera_id, direction, stream_url
        self.roi = roi                      # ROI dang ti le 0..1, co the doi luc dang chay
        self.engine = engine
        self.detect_every, self.save_seconds = detect_every, save_seconds
        self.max_frames, self.realtime = max_frames, realtime
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.latest_jpeg: bytes | None = None
        self.latest_counts: dict | None = None
        self.error: str | None = None

    def run(self):
        detections, last_save = [], time.monotonic()
        try:
            frames = self.engine.doc_khung_hinh(self.stream_url, self.max_frames)
            for i, frame in enumerate(frames):
                if self.stop_event.is_set():
                    break
                h, w = frame.shape[:2]
                roi_px = roi_sang_pixel(self.roi, w, h)
                if i % self.detect_every == 0 and self.engine.detector is not None:
                    detections = self.engine.phat_hien_xe(frame)
                    with self.lock:
                        self.latest_counts = self.engine.dem_xe(detections, roi_px)
                img = self.engine.ve_ket_qua(frame, detections, roi_px, self.latest_counts)
                with self.lock:
                    self.latest_jpeg = self.engine.ma_hoa_jpeg(img)
                if self.latest_counts and time.monotonic() - last_save >= self.save_seconds:
                    self.luu_so_xe(self.latest_counts)
                    last_save = time.monotonic()
                if self.realtime:
                    time.sleep(1 / STREAM_FPS)
        except FileNotFoundError as e:
            self.error = str(e)

    def luu_so_xe(self, counts: dict):
        db = SessionLocal()
        try:
            breakdown = {c: counts[c] for c in ("car", "motorbike", "bus", "truck")}
            db.add(models.TrafficCount(camera_id=self.camera_id, vehicle_count=counts["total"],
                                       breakdown=breakdown, density_score=counts["density"]))
            db.commit()
        finally:
            db.close()

    def lay_khung_hinh(self) -> bytes | None:
        with self.lock:
            return self.latest_jpeg

    def lay_so_xe(self) -> dict | None:
        with self.lock:
            return dict(self.latest_counts) if self.latest_counts else None

    def stop(self):
        self.stop_event.set()


class WorkerManager:
    """Quan ly 4 CameraWorker; dung chung 1 VisionEngine (1 mo hinh YOLO)."""

    def __init__(self):
        self.workers: dict[str, CameraWorker] = {}

    def start_all(self):
        engine = VisionEngine(tao_detector())
        db = SessionLocal()
        try:
            for cam in db.query(models.Camera).all():
                roi = (cam.roi_config or {}).get("polygon")
                w = CameraWorker(cam.id, cam.direction, cam.stream_url, roi, engine)
                self.workers[cam.direction] = w
                w.start()
        finally:
            db.close()

    def stop_all(self):
        for w in self.workers.values():
            w.stop()
        self.workers.clear()

    def get(self, direction: str) -> CameraWorker | None:
        return self.workers.get(direction)


manager = WorkerManager()
