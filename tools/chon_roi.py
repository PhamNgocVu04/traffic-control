"""Chon vung ROI (vung lan duong de dem xe) bang chuot.
Cach dung (server phai dang chay):   python tools/chon_roi.py North
  - Chuot trai : them 1 diem          - Chuot phai : xoa diem vua them
  - Enter      : luu ROI len server    - C          : xoa het lam lai
  - Esc        : thoat khong luu       - R          : bo ROI (dem ca khung hinh)"""
import json
import sys
import urllib.request

import cv2
import numpy as np

SERVER = "http://127.0.0.1:8000"
SHOW_WIDTH = 960  # hien thi to hon de click chinh xac


def goi_api(method: str, path: str, data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(SERVER + path, data=body, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def lay_khung_hinh_dau(stream_url: str):
    cap = cv2.VideoCapture(stream_url)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise SystemExit(f"Khong doc duoc video: {stream_url}")
    h, w = frame.shape[:2]
    return cv2.resize(frame, (SHOW_WIDTH, int(h * SHOW_WIDTH / w)))


def chuan_hoa(points, width: int, height: int):
    """Doi toa do pixel -> ti le 0..1 (ROI dung duoc cho moi do phan giai)."""
    return [[round(x / width, 3), round(y / height, 3)] for x, y in points]


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Cach dung: python tools/chon_roi.py North|South|East|West")
    direction = sys.argv[1]
    cams = {c["direction"]: c for c in goi_api("GET", "/api/cameras")}
    if direction not in cams:
        raise SystemExit(f"Khong co camera huong {direction}")
    frame = lay_khung_hinh_dau(cams[direction]["stream_url"])
    h, w = frame.shape[:2]
    points, win = [], f"Chon ROI - {direction}"

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((x, y))
        elif event == cv2.EVENT_RBUTTONDOWN and points:
            points.pop()

    cv2.namedWindow(win)
    cv2.setMouseCallback(win, on_mouse)
    while True:
        img = frame.copy()
        for p in points:
            cv2.circle(img, p, 4, (0, 255, 255), -1)
        if len(points) >= 2:
            cv2.polylines(img, [np.array(points, dtype=np.int32)], len(points) >= 3, (255, 255, 0), 2)
        cv2.putText(img, "Trai: them diem | Phai: xoa | Enter: luu | C: lam lai | R: bo ROI | Esc: thoat",
                    (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.imshow(win, img)
        key = cv2.waitKey(20) & 0xFF
        if key == 27:                        # Esc
            print("Da thoat, khong luu.")
            break
        if key in (ord("c"), ord("C")):
            points.clear()
        if key in (ord("r"), ord("R")):
            print(goi_api("PUT", f"/api/cameras/{direction}/roi", {"polygon": None}))
            break
        if key == 13:                        # Enter
            if len(points) < 3:
                print("Can it nhat 3 diem.")
                continue
            print(goi_api("PUT", f"/api/cameras/{direction}/roi", {"polygon": chuan_hoa(points, w, h)}))
            break
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
