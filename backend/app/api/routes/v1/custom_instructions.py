"""Custom instruction API routes."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, InstructionSvc
from app.schemas.custom_instruction import (
    InstructionCreate,
    InstructionList,
    InstructionRead,
    InstructionUpdate,
)

router = APIRouter(prefix="/custom-instructions", tags=["custom-instructions"])


@router.get("", response_model=InstructionList)
async def list_instructions(
    service: InstructionSvc,
    user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    items, total = await service.list_for_user(user_id=user.id, skip=skip, limit=limit)
    return InstructionList(items=items, total=total)


@router.post("", response_model=InstructionRead, status_code=status.HTTP_201_CREATED)
async def create_instruction(
    data: InstructionCreate, service: InstructionSvc, user: CurrentUser,
) -> Any:
    return await service.create(user_id=user.id, data=data)


@router.get("/{instruction_id}", response_model=InstructionRead)
async def get_instruction(
    instruction_id: UUID, service: InstructionSvc, user: CurrentUser,
) -> Any:
    return await service.get_by_id(instruction_id, user_id=user.id)


@router.patch("/{instruction_id}", response_model=InstructionRead)
async def update_instruction(
    instruction_id: UUID, data: InstructionUpdate,
    service: InstructionSvc, user: CurrentUser,
) -> Any:
    return await service.update(user_id=user.id, instruction_id=instruction_id, data=data)


@router.delete("/{instruction_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_instruction(
    instruction_id: UUID, service: InstructionSvc, user: CurrentUser,
) -> None:
    await service.delete(user_id=user.id, instruction_id=instruction_id)
