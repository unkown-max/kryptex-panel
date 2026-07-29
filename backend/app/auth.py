import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pasarguard import PasarguardAPI
from pydantic import BaseModel

from .config import COOKIE_NAME, COOKIE_SECURE, SESSION_TTL_SECONDS
from .pasarguard_client import get_client
from .sessions import SessionData, create_session, delete_session, get_session

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginPayload(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(payload: LoginPayload, response: Response, api: PasarguardAPI = Depends(get_client)):
    try:
        token = await api.get_token(username=payload.username, password=payload.password)
        admin = await api.get_current_admin(token=token.access_token)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (401, 403):
            raise HTTPException(status_code=401, detail="Kullanıcı adı veya şifre hatalı")
        raise HTTPException(status_code=502, detail="PasarGuard panele ulaşılamadı")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="PasarGuard panele ulaşılamadı")

    # Different PasarGuard/client versions expose this differently: some have a plain
    # `is_sudo` boolean, newer ones use a `role` field (e.g. "owner"/"sudo"/"operator").
    # Read it defensively so we don't crash on a version we haven't seen yet.
    admin_data = admin.model_dump() if hasattr(admin, "model_dump") else dict(admin)
    is_sudo = bool(admin_data.get("is_sudo")) or str(admin_data.get("role", "")).lower() in (
        "sudo",
        "owner",
    )

    session_id = create_session(
        username=admin_data.get("username", payload.username), token=token.access_token, is_sudo=is_sudo
    )
    response.set_cookie(
        key=COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=SESSION_TTL_SECONDS,
        path="/",
    )
    return {"ok": True, "username": admin_data.get("username", payload.username), "is_sudo": is_sudo}


@router.post("/logout")
async def logout(request: Request, response: Response):
    delete_session(request.cookies.get(COOKIE_NAME))
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}


def require_session(request: Request) -> SessionData:
    session = get_session(request.cookies.get(COOKIE_NAME))
    if not session:
        raise HTTPException(status_code=401, detail="Oturum bulunamadı, lütfen giriş yapın")
    return session


def require_sudo(session: SessionData = Depends(require_session)) -> SessionData:
    if not session["is_sudo"]:
        raise HTTPException(status_code=403, detail="Bu alan yalnızca yöneticiye açık")
    return session


@router.get("/me")
async def me(session: SessionData = Depends(require_session)):
    return {"username": session["username"], "is_sudo": session["is_sudo"]}
