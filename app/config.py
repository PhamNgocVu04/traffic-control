import os

# Mac dinh dung SQLite de ca nhom chay ngay khong can cai PostgreSQL.
# Khi dung PostgreSQL: set bien moi truong
#   DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/traffic
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./traffic.db")

# Thong so an toan den tin hieu (theo tieu chi nghiem thu US-02, US-03)
GREEN_MIN = 10      # giay
GREEN_MAX = 60      # giay
YELLOW_TIME = 3     # giay, co dinh
