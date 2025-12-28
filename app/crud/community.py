from typing import List, Optional, Dict, Any, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_
from sqlalchemy.orm import selectinload
import uuid

from ..models.community import Community, CommunityMember, CommunityType
from ..models.user import User
from ..schemas.community import CommunityCreate, CommunityUpdate
from .base import CRUDBase


class CRUDCommunity(CRUDBase[Community, CommunityCreate, CommunityUpdate]):
    async def create_with_creator(
        self, db: AsyncSession, *, obj_in: CommunityCreate, creator_id: uuid.UUID
    ) -> Community:
        db_obj = Community(
            **obj_in.model_dump(),
            creator_id=creator_id,
            member_count=1,  # Creator is first member
        )
        
        db.add(db_obj)
        await db.flush()
        
        # Add creator as admin member
        member = CommunityMember(
            community_id=db_obj.id,
            user_id=creator_id,
            is_admin=True,
        )
        db.add(member)
        await db.flush()
        
        return db_obj
    
    async def get_with_details(
        self, db: AsyncSession, id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[Community]:
        query = select(Community).options(
            selectinload(Community.creator)
        ).filter(Community.id == id)
        
        result = await db.execute(query)
        community = result.scalar_one_or_none()
        
        if community and user_id:
            # Check if user is member/admin
            member_result = await db.execute(
                select(CommunityMember).filter(
                    CommunityMember.community_id == community.id,
                    CommunityMember.user_id == user_id
                )
            )
            member = member_result.scalar_one_or_none()
            
            community.is_member = member is not None
            community.is_admin = member.is_admin if member else False
        
        return community
    
    async def search(
        self, db: AsyncSession, *, query: str, type_filter: Optional[CommunityType] = None,
        skip: int = 0, limit: int = 20
    ) -> List[Community]:
        query_builder = select(Community).options(selectinload(Community.creator))
        
        filters = []
        if query:
            filters.append(or_(
                Community.name.ilike(f"%{query}%"),
                Community.description.ilike(f"%{query}%"),
            ))
        
        if type_filter:
            filters.append(Community.type == type_filter)
        
        if filters:
            query_builder = query_builder.filter(and_(*filters))
        
        query_builder = query_builder.order_by(
            Community.member_count.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query_builder)
        return cast(List[Community], result.scalars().all())
     
     
    
    async def join_community(
        self,
        db: AsyncSession,
        *,
        community_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        # Check if community exists
        community_result = await db.execute(
            select(Community).where(Community.id == community_id)
        )
        community = community_result.scalar_one_or_none()

        if not community:
            return {
                "joined": False,
                "message": "Community not found",
            }

        # Check if already a member
        member_result = await db.execute(
            select(CommunityMember).where(
                CommunityMember.community_id == community_id,
                CommunityMember.user_id == user_id,
            )
        )
        existing = member_result.scalar_one_or_none()

        if existing:
            return {
                "joined": False,
                "message": "User is already a member of this community",
            }

        # Create membership
        member = CommunityMember(
            community_id=community_id,
            user_id=user_id,
            is_admin=False,
        )
        db.add(member)

        # Increment member count
        community.member_count += 1

        await db.commit()

        return {
            "joined": True,
            "member_count": community.member_count,
        }
    
    
    async def leave_community(
        self,
        db: AsyncSession,
        *,
        community_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        # Check if membership exists
        member_result = await db.execute(
            select(CommunityMember).where(
                CommunityMember.community_id == community_id,
                CommunityMember.user_id == user_id,
            )
        )
        member = member_result.scalar_one_or_none()

        if not member:
            return {
                "left": False,
                "message": "User is not a member of this community",
            }

        # Prevent creator from leaving (optional but recommended)
        if member.is_admin:
            return {
                "left": False,
                "message": "Community admin cannot leave the community",
            }

        await db.delete(member)

        # Decrement member count
        community = (
            await db.execute(
                select(Community).where(Community.id == community_id)
            )
        ).scalar_one()

        community.member_count = max(0, community.member_count - 1)

        await db.commit()

        return {
            "left": True,
            "member_count": community.member_count,
        }

    
    async def get_members(
        self,
        db: AsyncSession,
        *,
        community_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ):
        result = await db.execute(
            select(CommunityMember)
            .options(selectinload(CommunityMember.user))
            .filter(CommunityMember.community_id == community_id)
            .order_by(CommunityMember.joined_at.asc())
            .offset(skip)
            .limit(limit)
        )

        return result.scalars().all()
    
    async def get_user_communities(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> List[Community]:
        result = await db.execute(
            select(Community).options(selectinload(Community.creator)).join(
                CommunityMember
            ).filter(
                CommunityMember.user_id == user_id
            ).order_by(CommunityMember.joined_at.desc())
        )
        
        return cast(List[Community], result.scalars().all())


def get_community_crud():
    return CRUDCommunity(Community)