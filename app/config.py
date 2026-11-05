import os

# Mac dinh dung SQLite de ca nhom chay ngay khong can cai PostgreSQL.
# Khi dung PostgreSQL: set bien moi truong
#   DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/traffic
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./traffic.db")

# Thong so an toan den tin hieu (theo tieu chi nghiem thu US-02, US-03)
GREEN_MIN = 10      # giay
GREEN_MAX = 60      # giay
YELLOW_TIME = 3     # giay, co dinh

# Sprint 2: nhan dien xe
YOLO_MODEL = os.getenv("YOLO_MODEL", "yolov8n.pt")
YOLO_CONF = 0.15            # nguong tin cay toi thieu
DETECT_EVERY_N_FRAMES = 5   # 10 khung/giay -> nhan dien 2 lan/giay moi camera
SAVE_COUNT_SECONDS = 5      # bao lau ghi so xe vao bang traffic_counts 1 lan

# Sprint 3: dieu khien Auto
SMOOTH_WINDOW = 5           # lay trung binh 5 lan dem gan nhat cho so lieu on dinh
FIXED_GREEN = 30            # giay xanh co dinh khi khong co so lieu camera (du phong)
CONTROL_TICK = 0.5          # giay; vong dieu khien kiem tra den bao lau 1 lan
