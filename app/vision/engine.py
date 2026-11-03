"""VisionEngine: doc video, phat hien va dem xe theo ROI.
Sprint 1: doc video (lap lai khi het) va thu nho khung hinh.
Sprint 2: phat hien va dem xe bang YOLOv8."""
import time

import cv2

VEHICLE_CLASSES = ("car", "motorbike", "bus", "truck")
FRAME_WIDTH = 640   # thu nho khung hinh de 4 luong chay muot (video goc co the la 4K)
STREAM_FPS = 10     # so khung hinh/giay gui len Dashboard


class VisionEngine:
    def __init__(self, model_path: str = "yolov8n.pt"):
        self.model_path = model_path
        self.model = None  # TODO Sprint 2: from ultralytics import YOLO; self.model = YOLO(model_path)

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

    def mjpeg_stream(self, stream_url: str, max_frames: int | None = None):
        """Dong goi khung hinh thanh luong MJPEG de trinh duyet hien thi trong the <img>."""
        for frame in self.doc_khung_hinh(stream_url, max_frames):
            ok, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if not ok:
                continue
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n"
            if max_frames is None:
                time.sleep(1 / STREAM_FPS)

    def phat_hien_xe(self, frame) -> list[dict]:
        """TODO Sprint 2: chay YOLO, tra ve [{'cls':'car','box':(x1,y1,x2,y2)}, ...]."""
        raise NotImplementedError

    def dem_xe(self, detections: list[dict], roi_polygon: list) -> dict:
        """TODO Sprint 2: dem xe co tam box nam trong roi_polygon, chia theo loai."""
        raise NotImplementedError
