"""TrafficController: che do AUTO/MANUAL, tinh thoi gian xanh va chuyen pha theo thoi gian thuc.
Ham tick(now) duoc goi deu dan (moi 0.5 giay) boi vong dieu khien chay nen."""
import threading

from app.config import GREEN_MIN, GREEN_MAX, YELLOW_TIME, FIXED_GREEN
from app.controller.state_machine import PhaStateMachine, PAIRS, cap_con_lai


class TrafficController:
    def __init__(self, density_source=None, on_change=None):
        self.mode = "AUTO"
        self.state_machine = PhaStateMachine()
        self.density_source = density_source  # ham tra ve {"North-South": x, "East-West": y} hoac None
        self.on_change = on_change            # ham goi lai khi den doi mau (de ghi CSDL)
        self.lock = threading.RLock()
        self.green_end = None                 # thoi diem het xanh (chi dung o AUTO)
        self.green_duration = 0
        self.yellow_end = None                # thoi diem het vang
        self.pending_target = None            # cap se duoc xanh sau khi het vang
        self.last_density = None
        self.fallback = False                 # True = khong co so lieu camera, dung FIXED_GREEN

    # ---------- tinh toan ----------
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

    def _thoi_gian_xanh_cho(self, pair: str) -> int:
        density = self.density_source() if self.density_source else None
        self.last_density = density
        if not density:
            self.fallback = True
            return FIXED_GREEN
        self.fallback = False
        return self.tinh_thoi_luong_xanh(density["North-South"], density["East-West"])[pair]

    def _bao(self, pair, color, duration):
        if self.on_change:
            self.on_change(pair, color, duration, self.mode)

    # ---------- chuyen pha co den vang ----------
    def _bat_dau_chuyen(self, target: str, now: float) -> list[dict]:
        old = self.state_machine.bat_vang()
        if old is None:                       # dang do het -> bat xanh luon
            steps = self.state_machine.ket_thuc_vang(target)
            self._bat_dau_xanh(target, now)
            return steps
        self.pending_target = target
        self.yellow_end = now + YELLOW_TIME
        self.green_end = None
        self._bao(old, "YELLOW", YELLOW_TIME)
        return [{old: "YELLOW"}]

    def _bat_dau_xanh(self, pair: str, now: float):
        if self.mode == "AUTO":
            self.green_duration = self._thoi_gian_xanh_cho(pair)
            self.green_end = now + self.green_duration
        else:                                 # MANUAL: xanh cho den khi dieu phoi vien doi
            self.green_duration, self.green_end = 0, None
        self._bao(pair, "GREEN", self.green_duration)

    def tick(self, now: float):
        """Goi deu dan. Xu ly het vang, het xanh (AUTO) va bat dau chu ky moi."""
        with self.lock:
            if self.yellow_end is not None:
                if now >= self.yellow_end:
                    target, self.yellow_end, self.pending_target = self.pending_target, None, None
                    self.state_machine.ket_thuc_vang(target)
                    self._bat_dau_xanh(target, now)
                return
            if self.mode != "AUTO":
                return
            active = self.state_machine.pha_hien_tai()
            if self.green_end is None:        # vua vao AUTO: tinh thoi gian cho pha dang xanh
                self._bat_dau_xanh(active, now)
            elif now >= self.green_end:       # het xanh -> chuyen sang cap con lai
                self._bat_dau_chuyen(cap_con_lai(active), now)

    # ---------- lenh tu nguoi dung ----------
    def chuyen_che_do(self, mode: str):
        if mode not in ("AUTO", "MANUAL", "FAILSAFE"):
            raise ValueError("Che do khong hop le")
        with self.lock:
            self.mode = mode
            self.green_end = None             # AUTO: tinh lai thoi gian xanh o tick tiep theo

    def ep_pha(self, direction_pair: str, now: float) -> list[dict]:
        """Chi duoc ep pha o che do MANUAL (US-03). Co den vang dem YELLOW_TIME giay."""
        if direction_pair not in PAIRS:
            raise ValueError(f"Cap huong khong hop le: {direction_pair}")
        with self.lock:
            if self.mode != "MANUAL":
                raise PermissionError("Phai chuyen sang MANUAL truoc khi ep pha")
            if self.yellow_end is not None:
                raise PermissionError("Dang chuyen pha (den vang), thu lai sau vai giay")
            if self.state_machine.pha_hien_tai() == direction_pair:
                return []
            return self._bat_dau_chuyen(direction_pair, now)

    def trang_thai(self, now: float | None = None) -> dict:
        with self.lock:
            remaining = None
            if now is not None:
                end = self.yellow_end if self.yellow_end is not None else self.green_end
                if end is not None:
                    remaining = max(0, round(end - now))
            return {"mode": self.mode, "lights": dict(self.state_machine.lights),
                    "active_pair": self.state_machine.pha_hien_tai(),
                    "remaining_seconds": remaining, "green_duration": self.green_duration,
                    "density": self.last_density, "fallback": self.fallback}


# Mot bo dieu khien dung chung cho ca ung dung (1 nut giao)
controller = TrafficController()
