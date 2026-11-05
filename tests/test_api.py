from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_tao_camera():
    r = client.post("/api/cameras", json={"name": "Cam_Test", "stream_url": "data/videos/north.mp4", "direction": "North"})
    assert r.status_code == 201 and r.json()["status"] == "online"


def test_manual_va_ghi_log():
    assert client.post("/api/control/force-phase", json={"direction_pair": "East-West"}).status_code == 409
    client.post("/api/control/mode", json={"mode": "MANUAL"})
    r = client.post("/api/control/force-phase", json={"direction_pair": "East-West"})
    assert r.status_code == 200 and r.json()["lights"]["North-South"] == "YELLOW"  # dang vang dem
    actions = [l["action"] for l in client.get("/api/logs").json()]
    assert "OVERRIDE_GREEN" in actions and "SWITCH_MANUAL" in actions


def test_co_san_4_camera():
    directions = {c["direction"] for c in client.get("/api/cameras").json()}
    assert {"North", "South", "East", "West"} <= directions


def test_stream_huong_sai():
    assert client.get("/api/stream/Abc").status_code == 404


def test_cau_hinh_roi():
    r = client.put("/api/cameras/North/roi", json={"polygon": [[0.1, 0.5], [0.9, 0.5], [0.9, 1.0], [0.1, 1.0]]})
    assert r.status_code == 200 and len(r.json()["roi"]["polygon"]) == 4
    assert client.put("/api/cameras/North/roi", json={"polygon": [[0, 0], [2, 2], [0, 1]]}).status_code == 422


def test_counts_khi_tat_worker():
    assert client.get("/api/counts").json() == {}
