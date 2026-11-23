"""Sprint 4 - Giam sat thoi gian thuc:
  WebSocket /ws/dashboard : day trang thai den, so xe, canh bao, nhat ky moi 1 giay (PB-05)
  GET /api/alerts         : canh bao un tac dang hieu luc (PB-06)
  GET /api/stats/history  : mat do theo thoi gian cho bieu do luu luong"""
import asyncio
import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app import models
from app.api.routes import lay_logs
from app.config import WS_PUSH_SECONDS
from app.controller.traffic_controller import controller
from app.database import SessionLocal, get_db
from app.services.alerts import monitor
from app.vision.worker import manager

router = APIRouter()


@router.get("/api/alerts")
def get_alerts():
    return monitor.dang_canh_bao()


@router.get("/api/stats/history")
def history(minutes: int = 10, bucket: int = 30, db: Session = Depends(get_db)):
    """Mat do trung binh moi `bucket` giay trong `minutes` phut gan nhat, tach theo huong."""
    minutes, bucket = max(1, min(minutes, 120)), max(5, min(bucket, 600))
    since = models.now() - timedelta(minutes=minutes)
    rows = (db.query(models.TrafficCount.timestamp, models.TrafficCount.density_score, models.Camera.direction)
            .join(models.Camera, models.Camera.id == models.TrafficCount.camera_id)
            .filter(models.TrafficCount.timestamp >= since).all())
    gom: dict[int, dict[str, list[float]]] = {}
    for ts, density, direction in rows:
        if density is None:
            continue
        key = int(ts.replace(tzinfo=timezone.utc).timestamp() // bucket)  # gom ban ghi cung khoang thoi gian
        gom.setdefault(key, {}).setdefault(direction, []).append(density)
    keys = sorted(gom)
    directions = ["North", "South", "East", "West"]
    series = {d: [round(sum(v) / len(v), 1) if (v := gom[k].get(d)) else None for k in keys] for d in directions}
    labels = [datetime.fromtimestamp(k * bucket, timezone.utc).isoformat() for k in keys]
    return {"labels": labels, "series": series}


def goi_du_lieu() -> dict:
    """Mot goi du lieu day len dashboard."""
    db = SessionLocal()
    try:
        logs = lay_logs(db, 20)
    finally:
        db.close()
    return {"status": controller.trang_thai(time.monotonic()),
            "counts": {d: w.lay_so_xe() for d, w in manager.workers.items()},
            "alerts": monitor.dang_canh_bao(),
            "logs": logs,
            "server_time": models.iso_utc(models.now())}


@router.websocket("/ws/dashboard")
async def ws_dashboard(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.send_json(goi_du_lieu())
            await asyncio.sleep(WS_PUSH_SECONDS)
    except (WebSocketDisconnect, RuntimeError):
        pass  # trinh duyet dong tab -> ket thuc vong lap
