from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate
from .base import CRUDBase
from ..core.security import get_password_hash


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(
            select(User).filter(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        result = await db.execute(
            select(User).filter(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        # Hash password
        hashed_password = get_password_hash(obj_in.password)
        
        # Create user object
        db_obj = User(
            username=obj_in.username,
            email=obj_in.email,
            display_name=obj_in.display_name,
            hashed_password=hashed_password,
            role=obj_in.role,
            avatar_url=obj_in.avatar_url,
            college=obj_in.college,
            department=obj_in.department,
            bio=obj_in.bio,
            interests=obj_in.interests or [],
        )
        
        db.add(db_obj)
        await db.flush()
        return db_obj
    
    async def authenticate(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        user = await self.get_by_email(db, email)
        if not user:
            return None
        
        from ..core.security import verify_password
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    async def search(
        self, db: AsyncSession, *, query: str, skip: int = 0, limit: int = 20
    ) -> Sequence[User]:
        result = await db.execute(
            select(User).filter(
                or_(
                    User.username.ilike(f"%{query}%"),
                    User.display_name.ilike(f"%{query}%"),
                    User.email.ilike(f"%{query}%"),
                )
            ).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def update(
    self,
    db: AsyncSession,
    *,
    db_obj: User,
    obj_in: UserUpdate,
) -> User:
      update_data = obj_in.model_dump(exclude_unset=True)

      for field, value in update_data.items():
        setattr(db_obj, field, value)

      await db.commit()
      await db.refresh(db_obj)
      return db_obj

def get_user_crud():
    return CRUDUser(User)