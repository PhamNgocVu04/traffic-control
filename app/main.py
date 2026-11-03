from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.api.routes import router

Base.metadata.create_all(bind=engine)  # tao 5 bang neu chua co

app = FastAPI(title="Phan mem dieu khien giao thong tich hop camera", version="0.1.0")
app.include_router(router)

DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "dashboard"
app.mount("/dashboard", StaticFiles(directory=DASHBOARD_DIR, html=True), name="dashboard")


@app.get("/")
def root():
    return RedirectResponse("/dashboard/")
