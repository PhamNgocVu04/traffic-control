import os

# Cho test dung CSDL rieng, khong ghi lan vao traffic.db that
os.environ["DATABASE_URL"] = "sqlite:///./test_traffic.db"