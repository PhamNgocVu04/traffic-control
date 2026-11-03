"""VisionEngine: doc video, phat hien va dem xe theo ROI.
Sprint 1: doc video (lap lai khi het) va thu nho khung hinh.
Sprint 2: phat hien xe bang YOLOv8, dem xe trong vung ROI, ve ket qua."""
import threading
import time

import cv2
import numpy as np

from app.config import YOLO_MODEL, YOLO_CONF

FRAME_WIDTH = 640   # thu nho khung hinh de 4 luong chay muot (video goc co the la 4K)
STREAM_FPS = 10     # so khung hinh/giay gui len Dashboard

# Ma lop trong bo du lieu COCO ma YOLO da hoc -> ten loai xe dung trong du an
COCO_TO_VEHICLE = {2: "car", 3: "motorbike", 5: "bus", 7: "truck"}
VEHICLE_CLASSES = tuple(COCO_TO_VEHICLE.values())
# He so quy doi ra "xe con tuong duong" de tinh mat do (xe lon chiem nhieu cho hon)
PCU = {"car": 1.0, "motorbike": 0.3, "bus": 2.5, "truck": 2.5}
COLORS = {"car": (0, 200, 0), "motorbike": (255, 160, 0), "bus": (0, 140, 255), "truck": (0, 0, 230)}


class YoloDetector:
    """Boc YOLOv8. Nap mo hinh o lan dung dau tien; dung lock vi 4 camera dung chung 1 mo hinh."""

    def __init__(self, model_path: str = YOLO_MODEL, conf: float = YOLO_CONF):
        self.model_path, self.conf = model_path, conf
        self.model = None
        self.lock = threading.Lock()

    def detect(self, frame) -> list[dict]:
        with self.lock:
            if self.model is None:
                from ultralytics import YOLO  # import tai day de may chua cai YOLO van chay duoc Sprint 1
                self.model = YOLO(self.model_path)
            result = self.model(frame, classes=list(COCO_TO_VEHICLE), conf=self.conf, verbose=False)[0]
        out = []
        for box, cls, conf in zip(result.boxes.xyxy.tolist(), result.boxes.cls.tolist(), result.boxes.conf.tolist()):
            out.append({"cls": COCO_TO_VEHICLE[int(cls)], "box": tuple(int(v) for v in box), "conf": round(conf, 2)})
        return out


def tao_detector():
    """Tra ve YoloDetector neu da cai ultralytics, nguoc lai None (chi phat video, khong dem)."""
    try:
        import ultralytics  # noqa: F401
        return YoloDetector()
    except ImportError:
        return None


def roi_sang_pixel(roi, width: int, height: int):
    """ROI luu dang ti le 0..1 (khong phu thuoc do phan giai) -> doi sang toa do pixel.
    roi = None nghia la dem tren toan khung hinh."""
    if not roi:
        return None
    return np.array([[int(x * width), int(y * height)] for x, y in roi], dtype=np.int32)


class VisionEngine:
    def __init__(self, detector=None):
        self.detector = detector

    @staticmethod
    def thu_nho(frame, width: int = FRAME_WIDTH):
        """Giu nguyen ti le, thu nho chieu ngang ve `width` pixel."""
        h, w = frame.shape[:2]
        if w <= width:
            return frame
        return cv2.resize(frame, (width, int(h * width / w)))

    def doc_khung_hinh(self, stream_url: str, max_frames: int | None = None):
        """Generator: tra ve tung khung hinh da thu nho.
        Video file: het video thi quay lai tu dau (gia lap camera chay lien tuc).
        max_frames: chi dung cho test, de generator dung lai."""
        cap = cv2.VideoCapture(stream_url)
        if not cap.isOpened():
            raise FileNotFoundError(f"Khong mo duoc nguon video: {stream_url}")
        count = 0
        try:
            while max_frames is None or count < max_frames:
                ok, frame = cap.read()
                if not ok:                               # het video
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # tua ve dau
                    ok, frame = cap.read()
                    if not ok:
                        break
                count += 1
                yield self.thu_nho(frame)
        finally:
            cap.release()

    @staticmethod
    def ma_hoa_jpeg(frame) -> bytes:
        ok, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        return jpg.tobytes() if ok else b""

    @staticmethod
    def dong_goi_mjpeg(jpg: bytes) -> bytes:
        return b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n"

    def mjpeg_stream(self, stream_url: str, max_frames: int | None = None):
        """Phat video tho (khong nhan dien). Dung khi chua chay CameraWorker."""
        for frame in self.doc_khung_hinh(stream_url, max_frames):
            jpg = self.ma_hoa_jpeg(frame)
            if not jpg:
                continue
            yield self.dong_goi_mjpeg(jpg)
            if max_frames is None:
                time.sleep(1 / STREAM_FPS)

    def phat_hien_xe(self, frame) -> list[dict]:
        """Tra ve [{'cls': 'car', 'box': (x1, y1, x2, y2), 'conf': 0.87}, ...]."""
        if self.detector is None:
            return []
        return self.detector.detect(frame)

    @staticmethod
    def dem_xe(detections: list[dict], roi_polygon=None) -> dict:
        """Dem xe co diem giua canh duoi box (vi tri banh xe tren mat duong) nam trong ROI."""
        counts = {c: 0 for c in VEHICLE_CLASSES}
        for d in detections:
            x1, y1, x2, y2 = d["box"]
            point = ((x1 + x2) / 2, y2)
            if roi_polygon is None or cv2.pointPolygonTest(roi_polygon, point, False) >= 0:
                counts[d["cls"]] += 1
        counts["total"] = sum(counts[c] for c in VEHICLE_CLASSES)
        counts["density"] = round(sum(counts[c] * PCU[c] for c in VEHICLE_CLASSES), 1)
        return counts

    @staticmethod
    def ve_ket_qua(frame, detections: list[dict], roi_polygon, counts: dict | None):
        """Ve vung ROI, khung tung xe va dong chu tong so xe len khung hinh."""
        img = frame.copy()
        if roi_polygon is not None:
            cv2.polylines(img, [roi_polygon], True, (255, 255, 0), 2)
        for d in detections:
            x1, y1, x2, y2 = d["box"]
            color = COLORS[d["cls"]]
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img, d["cls"], (x1, max(y1 - 4, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        if counts is not None:
            cv2.rectangle(img, (0, 0), (230, 26), (0, 0, 0), -1)
            cv2.putText(img, f"Xe: {counts['total']}  Mat do: {counts['density']}", (6, 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        return img
