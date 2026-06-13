"""API key management — create, list, revoke per-user API keys."""

import secrets
from typing import Any
from uuid import UUID

import bcrypt
from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DBSession
from app.repositories import api_key as api_key_repo
from app.schemas.api_key import ApiKeyCreate, ApiKeyList, ApiKeyRead, ApiKeyListItem

router = APIRouter(prefix="/me/api-keys", tags=["me:api-keys"])


def _generate_key() -> tuple[str, str]:
    """Generate a new API key. Returns (plain_key, prefix, hash)."""
    raw = "sk_" + secrets.token_hex(22)  # sk_ + 44 hex chars = 47 total
    prefix = raw[:10]  # "sk_" + first 7 hex chars
    key_hash = bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()
    return raw, prefix, key_hash


@router.post("", response_model=ApiKeyRead, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    db: DBSession, user: CurrentUser, data: ApiKeyCreate,
) -> Any:
    plain_key, prefix, key_hash = _generate_key()
    key = await api_key_repo.create(
        db, user_id=user.id, name=data.name,
        key_prefix=prefix, key_hash=key_hash)
    return ApiKeyRead(
        id=key.id, name=key.name, key=plain_key,
        created_at=key.created_at)


@router.get("", response_model=ApiKeyList)
async def list_api_keys(
    db: DBSession, user: CurrentUser,
) -> Any:
    items, total = await api_key_repo.list_for_user(db, user_id=user.id)
    return ApiKeyList(
        items=[ApiKeyListItem.model_validate(k) for k in items],
        total=total)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def revoke_api_key(
    db: DBSession, user: CurrentUser, key_id: UUID,
) -> None:
    await api_key_repo.revoke(db, key_id=key_id, user_id=user.id)
