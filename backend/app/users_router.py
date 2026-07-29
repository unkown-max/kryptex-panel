import httpx
from fastapi import APIRouter, Depends, HTTPException
from pasarguard import PasarguardAPI, Tools, UserCreate, UserStatus
from pydantic import BaseModel, Field

from .auth import require_session
from .pasarguard_client import get_client
from .sessions import SessionData

router = APIRouter(prefix="/api/users", tags=["users"], dependencies=[Depends(require_session)])


class CreateUserPayload(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    data_limit_gb: float = Field(gt=0, description="Data cap in GB, e.g. 50")
    expire_days: int = Field(gt=0, description="Number of days until this account expires")
    note: str = ""
    group_ids: list[int] = Field(default_factory=lambda: [1])


@router.get("/groups")
async def list_groups(session: SessionData = Depends(require_session), api: PasarguardAPI = Depends(get_client)):
    """So the dashboard can offer a real dropdown instead of guessing group ids."""
    groups = await api.get_all_groups(token=session["token"])
    return [{"id": g.id, "name": g.name} for g in groups]


@router.get("")
async def list_users(session: SessionData = Depends(require_session), api: PasarguardAPI = Depends(get_client)):
    page = await api.get_users(token=session["token"], offset=0, limit=200)
    return [
        {
            "username": u.username,
            "status": u.status,
            "data_limit": u.data_limit,
            "used_traffic": u.used_traffic,
            "expire": u.expire,
            "note": u.note,
        }
        for u in page.users
    ]


@router.get("/summary")
async def users_summary(session: SessionData = Depends(require_session), api: PasarguardAPI = Depends(get_client)):
    page = await api.get_users(token=session["token"], offset=0, limit=200)
    total_users = len(page.users)
    active_users = sum(1 for u in page.users if str(u.status) == "active" or str(u.status) == "UserStatus.active")
    total_used = sum(u.used_traffic or 0 for u in page.users)
    return {"total_users": total_users, "active_users": active_users, "total_used_bytes": total_used}


@router.post("")
async def create_user(
    payload: CreateUserPayload,
    session: SessionData = Depends(require_session),
    api: PasarguardAPI = Depends(get_client),
):
    try:
        user = await api.create_user(
            UserCreate(
                username=payload.username,
                data_limit=Tools.gb(payload.data_limit_gb),
                expire=Tools.days(payload.expire_days),
                status=UserStatus.ACTIVE,
                group_ids=payload.group_ids,
                note=payload.note,
            ),
            token=session["token"],
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 409:
            raise HTTPException(status_code=409, detail="Bu kullanıcı adı zaten var")
        raise HTTPException(status_code=502, detail="PasarGuard kullanıcı oluşturamadı: " + exc.response.text)

    return {"ok": True, "username": user.username, "subscription_url": user.subscription_url}


@router.delete("/{username}")
async def delete_user(
    username: str,
    session: SessionData = Depends(require_session),
    api: PasarguardAPI = Depends(get_client),
):
    try:
        await api.remove_user(username, token=session["token"])
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 404:
            raise HTTPException(status_code=502, detail="PasarGuard kullanıcıyı silemedi")
    return {"ok": True}
