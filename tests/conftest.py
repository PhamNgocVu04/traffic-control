import os

# Cho test dung CSDL rieng, khong ghi lan vao traffic.db that
os.environ["DATABASE_URL"] = "sqlite:///./test_traffic.db"

# Xoa CSDL test cu de moi lan chay test deu bat dau tu du lieu sach
if os.path.exists("test_traffic.db"):
    os.remove("test_traffic.db")
