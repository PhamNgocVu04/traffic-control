"""PhaStateMachine: quan ly pha den, dam bao KHONG xung dot pha (US-02)."""

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
