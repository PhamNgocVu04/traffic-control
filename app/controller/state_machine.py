"""PhaStateMachine: quan ly pha den, dam bao KHONG xung dot pha (US-02)."""

PAIRS = ("North-South", "East-West")


def cap_con_lai(pair: str) -> str:
    return PAIRS[1] if pair == PAIRS[0] else PAIRS[0]


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

    def bat_vang(self) -> str | None:
        """Buoc 1 cua chuyen pha: cap dang xanh chuyen sang VANG. Tra ve cap do."""
        current = self.pha_hien_tai()
        if current == "ALL_RED":
            return None
        self.lights[current] = "YELLOW"
        return current

    def ket_thuc_vang(self, target_pair: str) -> list[dict]:
        """Buoc 2 (sau thoi gian vang): cap cu -> DO, roi cap moi -> XANH."""
        if target_pair not in PAIRS:
            raise ValueError(f"Cap huong khong hop le: {target_pair}")
        steps = []
        for p in PAIRS:
            if p != target_pair and self.lights[p] != "RED":
                self.lights[p] = "RED"; steps.append({p: "RED"})
        self.lights[target_pair] = "GREEN"; steps.append({target_pair: "GREEN"})
        assert not self.kiem_tra_xung_dot(), "Xung dot pha!"
        return steps

    def chuyen_pha(self, target_pair: str) -> list[dict]:
        """Chuyen pha tuc thi (khong cho het thoi gian vang). Dung cho test/tinh huong dac biet."""
        if target_pair not in PAIRS:
            raise ValueError(f"Cap huong khong hop le: {target_pair}")
        if self.pha_hien_tai() == target_pair:
            return []
        steps = []
        old = self.bat_vang()
        if old:
            steps.append({old: "YELLOW"})
        return steps + self.ket_thuc_vang(target_pair)
