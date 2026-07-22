from typing import Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.identity.models.user import User

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Retrieve a user by their UUID.
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by email address (case-insensitive or normalized lower).
        """
        result = await self.db.execute(select(User).where(User.email == email.lower().strip()))
        return result.scalar_one_or_none()

    async def exists_by_email(self, email: str) -> bool:
        """
        Check if a user exists with the given email address.
        """
        user = await self.get_by_email(email)
        return user is not None

    async def create(self, user: User) -> User:
        """
        Persist a new User model to the database.
        """
        user.email = user.email.lower().strip()
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user: User) -> User:
        """
        Commit changes to a User model.
        """
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
