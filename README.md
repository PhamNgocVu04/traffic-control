# Phần mềm điều khiển giao thông tích hợp camera — Nhóm 1

Sprint 0: bộ khung dự án (FastAPI + SQLAlchemy + Dashboard).

## Cài đặt và chạy

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Mở trình duyệt: http://127.0.0.1:8000 (Dashboard) — http://127.0.0.1:8000/docs (API).
Chạy test: `pytest -q`

Mặc định dùng SQLite (`traffic.db`). Dùng PostgreSQL: đặt biến môi trường
`DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/traffic`.

## Cấu trúc

| Thư mục | Phân hệ | Người phụ trách | Sprint |
|---|---|---|---|
| app/vision | Vision Engine (OpenCV, YOLOv8, ROI) | Dev AI | 1–2 |
| app/controller | Traffic Controller (State Machine, Auto/Manual) | Dev Backend | 3 |
| app/api, app/models.py | REST API, CSDL 5 bảng | Dev Backend | 0–4 |
| dashboard | Web Dashboard | Dev Frontend | 1, 4 |
| tests | pytest | Tester | mọi Sprint |
| data/videos | 4 video mô phỏng (không đẩy lên Git) | Cả nhóm | 0 |

## Quy ước Git
- `main`: bản ổn định để demo · `dev`: tích hợp · `feature/<ten>`: mỗi người một nhánh.
- Mỗi task: tạo nhánh từ `dev` → code + test → Pull Request vào `dev`.
