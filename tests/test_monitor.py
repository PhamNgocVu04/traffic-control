"""Sprint 4: canh bao un tac, lich su luu luong, WebSocket, gio UTC."""
from fastapi.testclient import TestClient

from app import models
from app.database import SessionLocal
from app.main import app
from app.services.alerts import CongestionMonitor

client = TestClient(app)


def test_canh_bao_sau_2_chu_ky_lien_tiep():
    m = CongestionMonitor(threshold=20, cycles=2)
    assert m.cap_nhat("North-South", 25) is None          # moi 1 chu ky -> chua bao
    assert m.cap_nhat("North-South", 30) == "RAISE"       # 2 chu ky lien tiep -> bao
    assert m.cap_nhat("North-South", 28) is None          # dang bao -> khong bao lap lai
    assert m.dang_canh_bao()[0]["cycles"] == 3
    assert m.cap_nhat("North-South", 10) == "CLEAR"       # giam duoi nguong -> het bao
    assert m.dang_canh_bao() == []


def test_khong_bao_neu_bi_ngat_quang():
    m = CongestionMonitor(threshold=20, cycles=2)
    m.cap_nhat("East-West", 25)
    m.cap_nhat("East-West", 5)                             # tut xuong -> dem lai tu dau
    assert m.cap_nhat("East-West", 25) is None
    assert m.cap_nhat("North-South", None) is None         # thieu so lieu -> bo qua


def test_api_alerts():
    assert client.get("/api/alerts").status_code == 200


def test_lich_su_luu_luong():
    db = SessionLocal()
    try:
        cam = db.query(models.Camera).filter(models.Camera.direction == "East").first()
        for d in (4.0, 6.0):
            db.add(models.TrafficCount(camera_id=cam.id, vehicle_count=3, density_score=d))
        db.commit()
    finally:
        db.close()
    h = client.get("/api/stats/history?minutes=5&bucket=60").json()
    assert h["labels"] and h["labels"][-1].endswith("+00:00")
    assert 5.0 in h["series"]["East"]                     # trung binh (4 + 6) / 2


def test_log_co_mui_gio_utc():
    client.post("/api/control/mode", json={"mode": "AUTO"})
    assert client.get("/api/logs").json()[0]["created_at"].endswith("+00:00")


def test_websocket_day_du_lieu():
    with client.websocket_connect("/ws/dashboard") as ws:
        d = ws.receive_json()
    assert {"status", "counts", "alerts", "logs", "server_time"} <= d.keys()
    assert d["status"]["mode"] in ("AUTO", "MANUAL")
