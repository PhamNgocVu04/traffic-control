"""Vong dieu khien chay nen: moi CONTROL_TICK giay goi controller.tick().
Noi controller voi so lieu dem xe (worker) va ghi trang thai den vao CSDL."""
import threading
import time

from app import models
from app.config import CONTROL_TICK
from app.database import SessionLocal
from app.controller.traffic_controller import controller
from app.services.alerts import monitor
from app.vision.worker import manager


def mat_do_theo_cap():
    """Cong mat do 2 huong doi dien. Thieu so lieu huong nao -> None (dung thoi gian co dinh)."""
    d = {k: (w.lay_so_xe() or {}).get("density") for k, w in manager.workers.items()}
    if any(d.get(k) is None for k in ("North", "South", "East", "West")):
        return None
    return {"North-South": d["North"] + d["South"], "East-West": d["East"] + d["West"]}


def ghi_trang_thai_den(pair, color, duration, mode):
    db = SessionLocal()
    try:
        db.add(models.TrafficLightState(direction_pair=pair, current_phase=color,
                                        duration_seconds=int(duration), mode=mode))
        # Sprint 4: moi lan 1 cap huong bat dau xanh = 1 chu ky -> kiem tra un tac cua cap do
        density = controller.last_density
        if color == "GREEN" and mode == "AUTO" and density:
            event = monitor.cap_nhat(pair, density.get(pair))
            if event == "RAISE":
                db.add(models.SystemLog(action_type="CONGESTION_ALERT",
                                        details=f"Un tac huong {pair}: mat do {density[pair]}"))
            elif event == "CLEAR":
                db.add(models.SystemLog(action_type="CONGESTION_CLEAR",
                                        details=f"Het un tac huong {pair}"))
        db.commit()
    finally:
        db.close()


class ControlLoop(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True, name="control-loop")
        self.stop_event = threading.Event()

    def run(self):
        while not self.stop_event.is_set():
            controller.tick(time.monotonic())
            self.stop_event.wait(CONTROL_TICK)

    def stop(self):
        self.stop_event.set()


def khoi_dong() -> ControlLoop:
    controller.density_source = mat_do_theo_cap
    controller.on_change = ghi_trang_thai_den
    loop = ControlLoop()
    loop.start()
    return loop
