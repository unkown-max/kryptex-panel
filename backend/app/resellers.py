import httpx
from fastapi import APIRouter, Depends, HTTPException
from pasarguard import AdminCreate, PasarguardAPI
from pydantic import BaseModel, Field

from . import db
from .auth import require_sudo
from .pasarguard_client import get_client
from .sessions import SessionData

router = APIRouter(prefix="/api/resellers", tags=["resellers"], dependencies=[Depends(require_sudo)])


class CreateResellerPayload(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6)
    display_name: str = ""
    plan: str = ""
    note: str = ""


@router.get("")
async def list_resellers(
    session: SessionData = Depends(require_sudo), api: PasarguardAPI = Depends(get_client)
):
    admins = await api.get_admins(token=session["token"])
    meta = db.get_all_reseller_meta()
    result = []
    for admin in admins:
        admin_data = admin.model_dump() if hasattr(admin, "model_dump") else dict(admin)
        admin_is_sudo = bool(admin_data.get("is_sudo")) or str(admin_data.get("role", "")).lower() in (
            "sudo",
            "owner",
        )
        if admin_is_sudo:
            continue  # don't list owner/sudo accounts as "resellers"
        username = admin_data.get("username")
        extra = meta.get(username, {})
        result.append(
            {
                "username": username,
                "display_name": extra.get("display_name", ""),
                "plan": extra.get("plan", ""),
                "note": extra.get("note", ""),
                "created_at": extra.get("created_at", ""),
                "users_usage": admin_data.get("used_traffic"),
            }
        )
    return result


@router.post("")
async def create_reseller(
    payload: CreateResellerPayload,
    session: SessionData = Depends(require_sudo),
    api: PasarguardAPI = Depends(get_client),
):
    try:
        await api.create_admin(
            AdminCreate(username=payload.username, password=payload.password, is_sudo=False),
            token=session["token"],
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 409:
            raise HTTPException(status_code=409, detail="Bu kullanıcı adı zaten kullanılıyor")
        raise HTTPException(status_code=502, detail="PasarGuard bayi oluşturamadı: " + exc.response.text)

    db.upsert_reseller_meta(
        username=payload.username,
        display_name=payload.display_name,
        plan=payload.plan,
        note=payload.note,
    )
    return {"ok": True}


@router.delete("/{username}")
async def delete_reseller(
    username: str,
    session: SessionData = Depends(require_sudo),
    api: PasarguardAPI = Depends(get_client),
):
    try:
        await api.remove_admin(username, token=session["token"])
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 404:
            raise HTTPException(status_code=502, detail="PasarGuard bayiyi silemedi")
    db.delete_reseller_meta(username)
    return {"ok": True}
