"""Custom instruction service — business logic layer."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories import custom_instruction as instruction_repo
from app.schemas.custom_instruction import InstructionCreate, InstructionUpdate


class InstructionService:
    """Service for managing custom instructions."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_for_user(
        self, *, user_id: UUID, skip: int = 0, limit: int = 50
    ) -> tuple[list, int]:
        return await instruction_repo.list_for_user(
            self.db, user_id=user_id, skip=skip, limit=limit
        )

    async def get_by_id(self, instruction_id: UUID, *, user_id: UUID):
        instruction = await instruction_repo.get_by_id(self.db, instruction_id=instruction_id)
        if not instruction or instruction.user_id != user_id:
            raise NotFoundError(
                message="Custom instruction not found",
                details={"instruction_id": str(instruction_id)},
            )
        return instruction

    async def create(self, *, user_id: UUID, data: InstructionCreate):
        if data.is_active:
            await instruction_repo.deactivate_others(
                self.db, user_id=user_id, exclude_id=UUID(int=0))
        return await instruction_repo.create(
            self.db, user_id=user_id, name=data.name,
            content=data.content, is_active=data.is_active)

    async def update(
        self, *, user_id: UUID, instruction_id: UUID, data: InstructionUpdate
    ):
        instruction = await self.get_by_id(instruction_id, user_id=user_id)
        update_data = data.model_dump(exclude_unset=True)
        if update_data.get("is_active") is True:
            await instruction_repo.deactivate_others(
                self.db, user_id=user_id, exclude_id=instruction_id)
        return await instruction_repo.update(
            self.db, db_instruction=instruction, update_data=update_data)

    async def delete(self, *, user_id: UUID, instruction_id: UUID) -> None:
        instruction = await self.get_by_id(instruction_id, user_id=user_id)
        await instruction_repo.delete_instruction(self.db, db_instruction=instruction)

    async def get_active_for_user(self, *, user_id: UUID) -> list:
        return await instruction_repo.get_active_for_user(self.db, user_id=user_id)
