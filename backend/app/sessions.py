"""
Very small in-memory session store.

Each session maps a random session id (kept only in an httpOnly cookie) to the
PasarGuard access token + role for that logged-in person. The PasarGuard token
itself never goes to the browser - only the random session id does.

Note: this is process-local. If you ever run more than one backend worker/
process behind a load balancer, swap this out for Redis (or a shared table) so
every worker can see the same sessions.
"""
import secrets
import time
from typing import Optional, TypedDict

from .config import SESSION_TTL_SECONDS


class SessionData(TypedDict):
    username: str
    token: str
    is_sudo: bool
    expires_at: float


_SESSIONS: dict[str, SessionData] = {}


def create_session(username: str, token: str, is_sudo: bool) -> str:
    session_id = secrets.token_urlsafe(32)
    _SESSIONS[session_id] = {
        "username": username,
        "token": token,
        "is_sudo": is_sudo,
        "expires_at": time.time() + SESSION_TTL_SECONDS,
    }
    return session_id


def get_session(session_id: Optional[str]) -> Optional[SessionData]:
    if not session_id:
        return None
    data = _SESSIONS.get(session_id)
    if not data:
        return None
    if data["expires_at"] < time.time():
        _SESSIONS.pop(session_id, None)
        return None
    return data


def delete_session(session_id: Optional[str]) -> None:
    if session_id:
        _SESSIONS.pop(session_id, None)
