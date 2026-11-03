import cv2
import numpy as np
import pytest

from app.vision.engine import VisionEngine, FRAME_WIDTH


@pytest.fixture
def video_4k(tmp_path):
    """Tao video gia 1280x720, 5 khung hinh de test (khong can video that)."""
    path = str(tmp_path / "fake.avi")
    out = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 10, (1280, 720))
    for i in range(5):
        out.write(np.full((720, 1280, 3), i * 40, dtype=np.uint8))
    out.release()
    return path


def test_doc_va_thu_nho(video_4k):
    frames = list(VisionEngine().doc_khung_hinh(video_4k, max_frames=3))
    assert len(frames) == 3
    assert frames[0].shape[1] == FRAME_WIDTH          # chieu ngang da thu nho ve 640


def test_het_video_thi_lap_lai(video_4k):
    frames = list(VisionEngine().doc_khung_hinh(video_4k, max_frames=12))  # video chi co 5 khung
    assert len(frames) == 12


def test_video_khong_ton_tai():
    with pytest.raises(FileNotFoundError):
        next(VisionEngine().doc_khung_hinh("khong_co_file.mp4"))


def test_mjpeg_dung_dinh_dang(video_4k):
    chunk = next(VisionEngine().mjpeg_stream(video_4k, max_frames=1))
    assert chunk.startswith(b"--frame\r\nContent-Type: image/jpeg")
