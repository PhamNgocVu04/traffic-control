"""VisionEngine: doc video, phat hien va dem xe theo ROI.
Sprint 0: chi co khung ham. Sprint 2 se cai dat bang OpenCV + YOLOv8."""

VEHICLE_CLASSES = ("car", "motorbike", "bus", "truck")


class VisionEngine:
    def __init__(self, model_path: str = "yolov8n.pt"):
        self.model_path = model_path
        self.model = None  # TODO Sprint 2: from ultralytics import YOLO; self.model = YOLO(model_path)

    def doc_khung_hinh(self, stream_url: str):
        """TODO Sprint 1: cv2.VideoCapture(stream_url) va tra ve tung frame."""
        raise NotImplementedError

    def phat_hien_xe(self, frame) -> list[dict]:
        """TODO Sprint 2: chay YOLO, tra ve [{'cls':'car','box':(x1,y1,x2,y2)}, ...]."""
        raise NotImplementedError

    def dem_xe(self, detections: list[dict], roi_polygon: list) -> dict:
        """TODO Sprint 2: dem xe co tam box nam trong roi_polygon, chia theo loai."""
        raise NotImplementedError
