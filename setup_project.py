"""Chay 1 lan: python setup_project.py  -> tao toan bo bo khung Sprint 0."""
from pathlib import Path

FILES = {}

FILES['requirements.txt'] = r'''fastapi==0.115.6
uvicorn[standard]==0.32.1
sqlalchemy==2.0.36
pydantic==2.10.4
httpx==0.28.1
pytest==8.3.4

# Bat khi dung PostgreSQL
# psycopg2-binary==2.9.10

# Bat o Sprint 1-2 (Vision Engine), cai nang ~2 GB
# opencv-python==4.10.0.84
# ultralytics==8.3.40

# Bat o Sprint 5 (xuat bao cao)
# pandas==2.2.3
# openpyxl==3.1.5
'''

FILES['.gitignore'] = r'''__pycache__/
*.pyc
.venv/
*.db
data/videos/*.mp4
*.pt
'''

FILES['README.md'] = r'''# Phần mềm điều khiển giao thông tích hợp camera — Nhóm 1

Sprint 0: bộ khung dự án (FastAPI + SQLAlchemy + Dashboard).

## Cài đặt và chạy

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Mở trình duyệt: http://127.0.0.1:8000 (Dashboard) — http://127.0.0.1:8000/docs (API).
Chạy test: `pytest -q`

Mặc định dùng SQLite (`traffic.db`). Dùng PostgreSQL: đặt biến môi trường
`DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/traffic`.

## Cấu trúc

| Thư mục | Phân hệ | Người phụ trách | Sprint |
|---|---|---|---|
| app/vision | Vision Engine (OpenCV, YOLOv8, ROI) | Dev AI | 1–2 |
| app/controller | Traffic Controller (State Machine, Auto/Manual) | Dev Backend | 3 |
| app/api, app/models.py | REST API, CSDL 5 bảng | Dev Backend | 0–4 |
| dashboard | Web Dashboard | Dev Frontend | 1, 4 |
| tests | pytest | Tester | mọi Sprint |
| data/videos | 4 video mô phỏng (không đẩy lên Git) | Cả nhóm | 0 |

## Quy ước Git
- `main`: bản ổn định để demo · `dev`: tích hợp · `feature/<ten>`: mỗi người một nhánh.
- Mỗi task: tạo nhánh từ `dev` → code + test → Pull Request vào `dev`.
'''

FILES['app/__init__.py'] = r''''''

FILES['app/config.py'] = r'''import os

# Mac dinh dung SQLite de ca nhom chay ngay khong can cai PostgreSQL.
# Khi dung PostgreSQL: set bien moi truong
#   DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/traffic
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./traffic.db")

# Thong so an toan den tin hieu (theo tieu chi nghiem thu US-02, US-03)
GREEN_MIN = 10      # giay
GREEN_MAX = 60      # giay
YELLOW_TIME = 3     # giay, co dinh
'''

FILES['app/database.py'] = r'''from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''

FILES['app/models.py'] = r'''from datetime import datetime, timezone

from sqlalchemy import BigInteger, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# BigInteger tren PostgreSQL, Integer tren SQLite (de autoincrement hoat dong)
BigId = BigInteger().with_variant(Integer, "sqlite")


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), default="operator")  # admin | operator
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Camera(Base):
    __tablename__ = "cameras"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    stream_url: Mapped[str] = mapped_column(String(255), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)  # North|South|East|West
    roi_config: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="online")  # online|offline|error


class TrafficCount(Base):
    __tablename__ = "traffic_counts"
    id: Mapped[int] = mapped_column(BigId, primary_key=True, autoincrement=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)
    vehicle_count: Mapped[int] = mapped_column(Integer, nullable=False)
    breakdown: Mapped[dict | None] = mapped_column(JSON)  # {"car":..,"motorbike":..,"bus":..,"truck":..}
    density_score: Mapped[float | None] = mapped_column(Float)


class TrafficLightState(Base):
    __tablename__ = "traffic_light_states"
    id: Mapped[int] = mapped_column(BigId, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)
    direction_pair: Mapped[str | None] = mapped_column(String(50))  # North-South | East-West
    current_phase: Mapped[str] = mapped_column(String(10), nullable=False)  # RED|YELLOW|GREEN
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False)  # AUTO|MANUAL|FAILSAFE


class SystemLog(Base):
    __tablename__ = "system_logs"
    id: Mapped[int] = mapped_column(BigId, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
'''

FILES['app/schemas.py'] = r'''from typing import Literal
from pydantic import BaseModel, ConfigDict


class CameraIn(BaseModel):
    name: str
    stream_url: str
    direction: Literal["North", "South", "East", "West"]
    roi_config: dict | None = None


class CameraOut(CameraIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str


class ModeIn(BaseModel):
    mode: Literal["AUTO", "MANUAL"]
    user_id: int | None = None


class ForcePhaseIn(BaseModel):
    direction_pair: Literal["North-South", "East-West"]
    user_id: int | None = None
'''

FILES['app/main.py'] = r'''from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.api.routes import router

Base.metadata.create_all(bind=engine)  # tao 5 bang neu chua co

app = FastAPI(title="Phan mem dieu khien giao thong tich hop camera", version="0.1.0")
app.include_router(router)

DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "dashboard"
app.mount("/dashboard", StaticFiles(directory=DASHBOARD_DIR, html=True), name="dashboard")


@app.get("/")
def root():
    return RedirectResponse("/dashboard/")
'''

FILES['app/api/__init__.py'] = r''''''

FILES['app/api/routes.py'] = r'''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.controller.traffic_controller import controller

router = APIRouter(prefix="/api")


def ghi_log(db: Session, action: str, details: str, user_id: int | None = None):
    db.add(models.SystemLog(user_id=user_id, action_type=action, details=details))
    db.commit()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/cameras", response_model=list[schemas.CameraOut])
def list_cameras(db: Session = Depends(get_db)):
    return db.query(models.Camera).all()


@router.post("/cameras", response_model=schemas.CameraOut, status_code=201)
def create_camera(data: schemas.CameraIn, db: Session = Depends(get_db)):
    cam = models.Camera(**data.model_dump())
    db.add(cam); db.commit(); db.refresh(cam)
    return cam


@router.get("/status")
def get_status():
    return controller.trang_thai()


@router.post("/control/mode")
def set_mode(data: schemas.ModeIn, db: Session = Depends(get_db)):
    controller.chuyen_che_do(data.mode)
    ghi_log(db, f"SWITCH_{data.mode}", f"Chuyen che do sang {data.mode}", data.user_id)
    return controller.trang_thai()


@router.post("/control/force-phase")
def force_phase(data: schemas.ForcePhaseIn, db: Session = Depends(get_db)):
    try:
        steps = controller.ep_pha(data.direction_pair)
    except PermissionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    ghi_log(db, "OVERRIDE_GREEN", f"Ep xanh {data.direction_pair}: {steps}", data.user_id)
    return {"steps": steps, **controller.trang_thai()}


@router.get("/logs")
def list_logs(limit: int = 20, db: Session = Depends(get_db)):
    rows = db.query(models.SystemLog).order_by(models.SystemLog.id.desc()).limit(limit).all()
    return [{"id": r.id, "action": r.action_type, "details": r.details,
             "created_at": r.created_at.isoformat()} for r in rows]
'''

FILES['app/controller/__init__.py'] = r''''''

FILES['app/controller/state_machine.py'] = r'''"""PhaStateMachine: quan ly pha den, dam bao KHONG xung dot pha (US-02)."""

PAIRS = ("North-South", "East-West")


class PhaStateMachine:
    def __init__(self):
        # Moi cap huong co 1 mau: GREEN | YELLOW | RED
        self.lights = {"North-South": "GREEN", "East-West": "RED"}

    def kiem_tra_xung_dot(self, lights: dict | None = None) -> bool:
        """True neu co xung dot: hai cap huong cung khong do (GREEN/YELLOW)."""
        lights = lights or self.lights
        active = [p for p, c in lights.items() if c != "RED"]
        return len(active) > 1

    def pha_hien_tai(self) -> str:
        return next((p for p, c in self.lights.items() if c != "RED"), "ALL_RED")

    def chuyen_pha(self, target_pair: str) -> list[dict]:
        """Chuyen xanh sang target_pair. Tra ve danh sach buoc da thuc hien.
        Thu tu an toan: XANH -> VANG -> DO (cap cu), roi DO -> XANH (cap moi)."""
        if target_pair not in PAIRS:
            raise ValueError(f"Cap huong khong hop le: {target_pair}")
        steps = []
        current = self.pha_hien_tai()
        if current == target_pair:
            return steps
        if current != "ALL_RED":
            self.lights[current] = "YELLOW"; steps.append({current: "YELLOW"})
            self.lights[current] = "RED";    steps.append({current: "RED"})
        self.lights[target_pair] = "GREEN";  steps.append({target_pair: "GREEN"})
        assert not self.kiem_tra_xung_dot(), "Xung dot pha!"
        return steps
'''

FILES['app/controller/traffic_controller.py'] = r'''"""TrafficController: che do AUTO/MANUAL/FAILSAFE va tinh thoi luong den xanh."""
from app.config import GREEN_MIN, GREEN_MAX
from app.controller.state_machine import PhaStateMachine


class TrafficController:
    def __init__(self):
        self.mode = "AUTO"
        self.state_machine = PhaStateMachine()

    def tinh_thoi_luong_xanh(self, density_ns: float, density_ew: float) -> dict:
        """Chia thoi gian xanh ty le thuan voi mat do moi cap huong (US-02).
        Ket qua luon nam trong [GREEN_MIN, GREEN_MAX]."""
        total = density_ns + density_ew
        if total <= 0:
            return {"North-South": GREEN_MIN, "East-West": GREEN_MIN}
        cycle = GREEN_MAX + GREEN_MIN  # tong thoi gian xanh cua 1 chu ky
        def clamp(x): return int(max(GREEN_MIN, min(GREEN_MAX, round(x))))
        return {"North-South": clamp(cycle * density_ns / total),
                "East-West": clamp(cycle * density_ew / total)}

    def chuyen_che_do(self, mode: str):
        if mode not in ("AUTO", "MANUAL", "FAILSAFE"):
            raise ValueError("Che do khong hop le")
        self.mode = mode

    def ep_pha(self, direction_pair: str) -> list[dict]:
        """Chi duoc ep pha o che do MANUAL (US-03)."""
        if self.mode != "MANUAL":
            raise PermissionError("Phai chuyen sang MANUAL truoc khi ep pha")
        return self.state_machine.chuyen_pha(direction_pair)

    def trang_thai(self) -> dict:
        return {"mode": self.mode, "lights": dict(self.state_machine.lights),
                "active_pair": self.state_machine.pha_hien_tai()}


# Mot bo dieu khien dung chung cho ca ung dung (1 nut giao)
controller = TrafficController()
'''

FILES['app/vision/__init__.py'] = r''''''

FILES['app/vision/engine.py'] = r'''"""VisionEngine: doc video, phat hien va dem xe theo ROI.
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
'''

FILES['dashboard/index.html'] = r'''<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<title>Dashboard điều khiển giao thông</title>
<style>
  body { font-family: Arial, sans-serif; margin: 24px; background: #EEF3F8; color: #1D3557; }
  .row { display: flex; gap: 16px; flex-wrap: wrap; }
  .card { background: #fff; border-radius: 10px; padding: 16px; min-width: 220px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
  .light { display: inline-block; width: 22px; height: 22px; border-radius: 50%; vertical-align: middle; margin-right: 8px; }
  .GREEN { background: #2A9D8F; } .YELLOW { background: #E9A424; } .RED { background: #C0392B; }
  button { padding: 8px 14px; margin: 4px 4px 0 0; cursor: pointer; }
  pre { background: #f7f7f7; padding: 8px; max-height: 220px; overflow: auto; }
</style>
</head>
<body>
<h1>Dashboard điều khiển giao thông</h1>
<div class="row">
  <div class="card"><h3>Chế độ</h3><p id="mode">-</p>
    <button onclick="setMode('AUTO')">Auto</button>
    <button onclick="setMode('MANUAL')">Manual</button></div>
  <div class="card"><h3>Đèn tín hiệu</h3><div id="lights">-</div></div>
  <div class="card"><h3>Ép pha (Manual)</h3>
    <button onclick="force('North-South')">Xanh Bắc - Nam</button>
    <button onclick="force('East-West')">Xanh Đông - Tây</button>
    <p id="msg"></p></div>
</div>
<div class="card" style="margin-top:16px"><h3>Nhật ký</h3><pre id="logs"></pre></div>

<script>
async function refresh() {
  const s = await (await fetch('/api/status')).json();
  document.getElementById('mode').textContent = s.mode;
  document.getElementById('lights').innerHTML = Object.entries(s.lights)
    .map(([k, v]) => `<p><span class="light ${v}"></span>${k}: ${v}</p>`).join('');
  const logs = await (await fetch('/api/logs')).json();
  document.getElementById('logs').textContent = logs.map(l => `${l.created_at}  ${l.action}  ${l.details}`).join('\n');
}
async function setMode(mode) {
  await fetch('/api/control/mode', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({mode})});
  refresh();
}
async function force(pair) {
  const r = await fetch('/api/control/force-phase', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({direction_pair: pair})});
  const d = await r.json();
  document.getElementById('msg').textContent = r.ok ? 'Đã ép pha ' + pair : d.detail;
  refresh();
}
refresh(); setInterval(refresh, 2000);  // Sprint 4: thay bang WebSocket
</script>
</body>
</html>
'''

FILES['tests/__init__.py'] = r''''''

FILES['tests/test_controller.py'] = r'''import pytest
from app.config import GREEN_MIN, GREEN_MAX
from app.controller.state_machine import PhaStateMachine
from app.controller.traffic_controller import TrafficController


def test_khong_xung_dot_pha():
    sm = PhaStateMachine()
    for pair in ["East-West", "North-South", "East-West"]:
        sm.chuyen_pha(pair)
        assert not sm.kiem_tra_xung_dot()


def test_chuyen_pha_co_den_vang():
    sm = PhaStateMachine()
    steps = sm.chuyen_pha("East-West")
    assert steps[0] == {"North-South": "YELLOW"}
    assert steps[-1] == {"East-West": "GREEN"}


def test_thoi_luong_xanh_nam_trong_bien():
    tc = TrafficController()
    for ns, ew in [(0, 0), (100, 1), (1, 100), (30, 30)]:
        g = tc.tinh_thoi_luong_xanh(ns, ew)
        assert all(GREEN_MIN <= v <= GREEN_MAX for v in g.values())


def test_ep_pha_phai_o_manual():
    tc = TrafficController()
    with pytest.raises(PermissionError):
        tc.ep_pha("East-West")
    tc.chuyen_che_do("MANUAL")
    assert tc.ep_pha("East-West")[-1] == {"East-West": "GREEN"}
'''

FILES['tests/test_api.py'] = r'''from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_tao_camera():
    r = client.post("/api/cameras", json={"name": "Cam_Huong_Bac", "stream_url": "data/videos/north.mp4", "direction": "North"})
    assert r.status_code == 201 and r.json()["status"] == "online"


def test_manual_va_ghi_log():
    assert client.post("/api/control/force-phase", json={"direction_pair": "East-West"}).status_code == 409
    client.post("/api/control/mode", json={"mode": "MANUAL"})
    r = client.post("/api/control/force-phase", json={"direction_pair": "East-West"})
    assert r.status_code == 200 and r.json()["lights"]["East-West"] == "GREEN"
    actions = [l["action"] for l in client.get("/api/logs").json()]
    assert "OVERRIDE_GREEN" in actions and "SWITCH_MANUAL" in actions
'''

FILES['data/videos/.gitkeep'] = r''''''

for path, content in FILES.items():
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print("Da tao:", path)
print("\nXong! Tiep theo: python -m venv .venv")