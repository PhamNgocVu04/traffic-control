"""Kiem thu vong dieu khien Auto bang thoi gian gia lap (khong phai cho that)."""
from app.config import YELLOW_TIME, FIXED_GREEN, GREEN_MIN, GREEN_MAX
from app.controller.traffic_controller import TrafficController
from app.vision.worker import CameraWorker


def chay(tc, tu, den):
    """Goi tick moi 0.5 giay tu thoi diem `tu` den `den`."""
    t = tu
    while t <= den:
        tc.tick(t)
        t += 0.5


def test_auto_huong_dong_xe_duoc_xanh_lau_hon():
    tc = TrafficController(density_source=lambda: {"North-South": 30, "East-West": 10})
    tc.tick(0)
    assert tc.state_machine.lights["North-South"] == "GREEN"
    assert tc.green_duration > tc.tinh_thoi_luong_xanh(30, 10)["East-West"]  # Bac-Nam dong hon


def test_auto_tu_doi_pha_khi_het_xanh():
    tc = TrafficController(density_source=lambda: {"North-South": 10, "East-West": 10})
    tc.tick(0)
    g = tc.green_duration
    chay(tc, 0.5, g)                                   # het xanh -> vang
    assert tc.state_machine.lights["North-South"] == "YELLOW"
    chay(tc, g + 0.5, g + YELLOW_TIME + 0.5)           # het vang -> doi pha
    assert tc.state_machine.lights == {"North-South": "RED", "East-West": "GREEN"}


def test_khong_bao_gio_xung_dot_trong_nhieu_chu_ky():
    tc = TrafficController(density_source=lambda: {"North-South": 50, "East-West": 5})
    for i in range(2000):                              # ~1000 giay, nhieu chu ky
        tc.tick(i * 0.5)
        assert not tc.state_machine.kiem_tra_xung_dot()
        assert GREEN_MIN <= tc.green_duration <= GREEN_MAX


def test_khong_co_so_lieu_thi_dung_thoi_gian_co_dinh():
    tc = TrafficController(density_source=lambda: None)
    tc.tick(0)
    assert tc.fallback and tc.green_duration == FIXED_GREEN


def test_manual_dung_auto_va_quay_lai():
    tc = TrafficController(density_source=lambda: {"North-South": 10, "East-West": 10})
    tc.tick(0)
    tc.chuyen_che_do("MANUAL")
    chay(tc, 0.5, 500)                                 # Manual: khong tu doi pha
    assert tc.state_machine.lights["North-South"] == "GREEN"
    tc.chuyen_che_do("AUTO")
    tc.tick(500)
    assert tc.green_end is not None                    # Auto chay lai, tinh thoi gian moi


def test_ghi_lai_moi_lan_doi_den():
    events = []
    tc = TrafficController(density_source=lambda: None, on_change=lambda *a: events.append(a))
    chay(tc, 0, FIXED_GREEN + YELLOW_TIME + 1)
    colors = [e[1] for e in events]
    assert colors == ["GREEN", "YELLOW", "GREEN"]


def test_lam_muot_so_dem():
    hist = [{"car": 4, "total": 4, "density": 4.0}, {"car": 12, "total": 12, "density": 12.0},
            {"car": 5, "total": 5, "density": 5.0}]
    c = CameraWorker.lam_muot(hist)
    assert c["total"] == 7 and c["density"] == 7.0
