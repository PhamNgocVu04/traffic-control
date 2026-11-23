"""Tu dong tim vung ROI (mat duong) cho camera bang cach theo doi chuyen dong.
Y tuong: cho video chay vai tram khung hinh, pixel nao thuong xuyen co xe chay qua
thi la mat duong; nha, cay, xe dau dung yen se bi loai.
Cach dung (server phai dang chay):
    python tools/auto_roi.py            -> tu dong cho ca 4 huong
    python tools/auto_roi.py North      -> chi 1 huong
Ket qua: ROI duoc luu len server + anh kiem tra roi_auto_<huong>.png trong thu muc tools/"""
import json
import os
import sys
import urllib.error
import urllib.request

import cv2
import numpy as np

SERVER = "http://127.0.0.1:8001"
WIDTH = 640            # xu ly tren khung hinh 640 px (giong VisionEngine)
SO_KHUNG = 600         # so khung hinh dung de hoc chuyen dong (~20 giay video 30 fps)
BO_QUA_DAU = 40        # bo qua cac khung dau khi bo tach nen chua on dinh
DIEN_TICH_TOI_THIEU = 0.01  # bo cac vung chuyen dong nho hon 1% khung hinh (la cay, nguoi)
THU_MUC = os.path.dirname(os.path.abspath(__file__))


def goi_api(method: str, path: str, data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(SERVER + path, data=body, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def ban_do_chuyen_dong(stream_url: str):
    """Tra ve (anh dau tien, ban do tan suat chuyen dong 0..1) cua video.
    Video quay bang drone luon troi nhe -> can chong rung: dua moi khung hinh ve
    dung vi tri khung dau tien roi moi tach nen, neu khong thi ca khung hinh deu 'chuyen dong'."""
    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        raise SystemExit(f"Khong doc duoc video: {stream_url}")
    tach_nen = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=40, detectShadows=False)
    dau = tong = so_lan = xam_truoc = None
    T = np.eye(3)                                # bien doi: khung hien tai -> khung dau tien
    for i in range(SO_KHUNG):
        ok, frame = cap.read()
        if not ok:
            break
        h, w = frame.shape[:2]
        frame = cv2.resize(frame, (WIDTH, int(h * WIDTH / w)))
        h, w = frame.shape[:2]
        xam = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if dau is None:
            dau = frame.copy()
            tong = np.zeros((h, w), np.float32)
            so_lan = np.zeros((h, w), np.float32)
        else:
            # Do chuyen dong cua camera giua 2 khung lien tiep bang cac diem goc (nha, vach ke duong)
            p0 = cv2.goodFeaturesToTrack(xam_truoc, 400, 0.01, 8)
            if p0 is not None:
                p1, st, _ = cv2.calcOpticalFlowPyrLK(xam_truoc, xam, p0, None)
                tot = st.ravel() == 1
                if tot.sum() >= 10:
                    # RANSAC bo qua cac diem tren xe dang chay, chi giu chuyen dong chung cua camera
                    M, _ = cv2.estimateAffinePartial2D(p1[tot], p0[tot], method=cv2.RANSAC,
                                                       ransacReprojThreshold=2)
                    if M is not None:
                        T = T @ np.vstack([M, [0, 0, 1]])
        xam_truoc = xam
        on_dinh = cv2.warpAffine(frame, T[:2], (w, h))
        hop_le = cv2.warpAffine(np.ones((h, w), np.uint8), T[:2], (w, h))
        hop_le = cv2.erode(hop_le, np.ones((25, 25), np.uint8))   # bo vien den sau khi xoay/dich anh
        mask = tach_nen.apply(cv2.GaussianBlur(on_dinh, (5, 5), 0))
        if i >= BO_QUA_DAU:
            tong += (mask > 0) & (hop_le > 0)
            so_lan += hop_le > 0
    cap.release()
    if so_lan is None or so_lan.max() == 0:
        raise SystemExit(f"Video qua ngan: {stream_url}")
    return dau, tong / np.maximum(so_lan, 1)


def tim_roi(tan_suat: np.ndarray):
    """Tu ban do tan suat -> da giac ROI (toa do pixel).
    Thu nguong tu thap len cao cho den khi ROI chiem 3%..60% khung hinh (hop ly voi mat duong)."""
    h, w = tan_suat.shape
    tan_suat = tan_suat.copy()
    le = 12                                   # bo 12 px sat mep: vung mep bi nhieu khi chong rung
    tan_suat[:le, :] = tan_suat[-le:, :] = 0
    tan_suat[:, :le] = tan_suat[:, -le:] = 0
    mask = np.zeros((h, w), np.uint8)
    for nguong in (0.03, 0.05, 0.08, 0.12, 0.2):
        mask = (tan_suat >= nguong).astype(np.uint8) * 255
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))       # xoa nhieu li ti
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))    # noi vet xe thanh dai duong
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        vung = [c for c in contours if cv2.contourArea(c) >= DIEN_TICH_TOI_THIEU * w * h]
        if not vung:
            continue
        lon_nhat = max(cv2.contourArea(c) for c in vung)
        vung = [c for c in vung if cv2.contourArea(c) >= 0.3 * lon_nhat]   # chi giu cac dai duong chinh
        hull = cv2.convexHull(np.vstack(vung))
        ti_le = cv2.contourArea(hull) / (w * h)
        if 0.03 <= ti_le <= 0.6:
            poly = cv2.approxPolyDP(hull, 0.01 * cv2.arcLength(hull, True), True)
            return poly.reshape(-1, 2), mask
    return None, mask


def luu_roi(direction: str, points):
    """Gui ROI len server. Thu lan luot cac dang du lieu ma API co the nhan."""
    for body in ({"polygon": points}, {"points": points}, points):
        try:
            return goi_api("PUT", f"/api/cameras/{direction}/roi", body)
        except urllib.error.HTTPError as e:
            if e.code != 422:   # 422 = sai dang du lieu -> thu dang khac
                raise
    raise SystemExit("Server khong nhan dinh dang ROI - kiem tra lai API")


def xu_ly(direction: str, cam: dict):
    print(f"[{direction}] dang phan tich chuyen dong...")
    anh, tan_suat = ban_do_chuyen_dong(cam["stream_url"])
    h, w = tan_suat.shape
    poly, mask = tim_roi(tan_suat)
    if poly is None:
        print(f"[{direction}] KHONG tim duoc mat duong ro rang -> giu ROI cu, hay ve tay: python tools/chon_roi.py {direction}")
        cv2.imwrite(os.path.join(THU_MUC, f"roi_auto_{direction}.png"), anh)
        return
    ti_le = cv2.contourArea(poly.astype(np.int32)) / (w * h)
    points = [[round(float(x) / w, 3), round(float(y) / h, 3)] for x, y in poly]
    luu_roi(direction, points)

    # Anh kiem tra: vung do = noi co chuyen dong, vien vang = ROI da luu
    xem = anh.copy()
    xem[mask > 0] = (0.6 * xem[mask > 0] + 0.4 * np.array([0, 0, 255])).astype(np.uint8)
    cv2.polylines(xem, [poly.astype(np.int32)], True, (0, 255, 255), 2)
    duong_dan = os.path.join(THU_MUC, f"roi_auto_{direction}.png")
    cv2.imwrite(duong_dan, xem)
    print(f"[{direction}] da luu ROI {len(points)} diem, chiem {ti_le:.0%} khung hinh -> xem {duong_dan}")


def main():
    cams = {c["direction"]: c for c in goi_api("GET", "/api/cameras")}
    huong = sys.argv[1:] or ["North", "South", "East", "West"]
    for d in huong:
        if d not in cams:
            print(f"Khong co camera huong {d}")
            continue
        xu_ly(d, cams[d])


if __name__ == "__main__":
    main()