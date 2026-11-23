import pytest
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
        tc.ep_pha("East-West", now=0)
    tc.chuyen_che_do("MANUAL")
    assert tc.ep_pha("East-West", now=0) == [{"North-South": "YELLOW"}]   # vang dem truoc
    tc.tick(now=3)                                                           # sau 3 giay vang
    assert tc.state_machine.lights == {"North-South": "RED", "East-West": "GREEN"}
