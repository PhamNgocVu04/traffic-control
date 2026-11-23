"""Canh bao un tac (PB-06): mat do 1 cap huong vuot nguong lien tiep CONGESTION_CYCLES chu ky den.
Can vuot nhieu chu ky lien tiep moi bao de tranh bao nham khi xe chi don lai trong chot lat."""
import threading

from app.config import CONGESTION_DENSITY, CONGESTION_CYCLES
from app.models import iso_utc, now


class CongestionMonitor:
    def __init__(self, threshold: float = CONGESTION_DENSITY, cycles: int = CONGESTION_CYCLES):
        self.threshold, self.cycles = threshold, cycles
        self.streak: dict[str, int] = {}     # so chu ky vuot nguong lien tiep cua moi cap huong
        self.alerts: dict[str, dict] = {}    # canh bao dang hieu luc
        self.lock = threading.Lock()

    def cap_nhat(self, pair: str, density: float | None) -> str | None:
        """Goi 1 lan moi chu ky. Tra ve 'RAISE' (bat dau un tac), 'CLEAR' (het un tac) hoac None."""
        if density is None:
            return None
        with self.lock:
            if density >= self.threshold:
                self.streak[pair] = self.streak.get(pair, 0) + 1
                if pair in self.alerts:          # dang canh bao -> chi cap nhat so lieu
                    self.alerts[pair].update(density=round(density, 1), cycles=self.streak[pair])
                    return None
                if self.streak[pair] >= self.cycles:
                    self.alerts[pair] = {"pair": pair, "density": round(density, 1),
                                         "cycles": self.streak[pair], "since": iso_utc(now())}
                    return "RAISE"
                return None
            self.streak[pair] = 0
            return "CLEAR" if self.alerts.pop(pair, None) is not None else None

    def dang_canh_bao(self) -> list[dict]:
        with self.lock:
            return [dict(a) for a in self.alerts.values()]

    def reset(self):
        with self.lock:
            self.streak.clear()
            self.alerts.clear()


monitor = CongestionMonitor()
