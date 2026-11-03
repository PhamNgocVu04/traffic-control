"""TrafficController: che do AUTO/MANUAL/FAILSAFE va tinh thoi luong den xanh."""
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
