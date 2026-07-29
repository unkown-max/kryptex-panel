from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import db
from .auth import router as auth_router
from .resellers import router as resellers_router
from .users_router import router as users_router

app = FastAPI(title="Kryptex Panel API")

db.init_db()

app.include_router(auth_router)
app.include_router(resellers_router)
app.include_router(users_router)

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
