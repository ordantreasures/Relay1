from fastapi import APIRouter, Depends, Query, Path, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from fastapi import Path, Depends, HTTPException
import uuid

from ..database import get_db
from ..crud.community import get_community_crud
from ..crud.post import get_post_crud
from ..schemas.community import CommunityCreate, CommunityUpdate, CommunityResponse
from ..schemas.community_member import CommunityMemberOut
from ..schemas.post import PostListResponse
from ..models.community import CommunityType
from ..core.errors import NotFoundError, ForbiddenError, APIError
from .dependencies import get_current_user, get_current_active_user, require_admin

router = APIRouter()

# Get multiple communities with filtering and pagination
@router.get("/", response_model=List[CommunityResponse])
async def get_communities(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    type_filter: Optional[CommunityType] = Query(None),
    query: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(current_user["id"]) if current_user else None
    
    community_crud = get_community_crud()
    communities = await community_crud.search(
        db,
        query=query or "",
        type_filter=type_filter,
        skip=skip,
        limit=limit,
    )
    
    # Check membership for each community
    for community in communities:
        if user_id:
            # This would be more efficient with a single query
            # For now, we'll get details for each
            detailed = await community_crud.get_with_details(db, community.id, user_id)
            if detailed:
                community.is_member = detailed.is_member
                community.is_admin = detailed.is_admin
    
    return communities

# Create a new community
@router.post("/", response_model=CommunityResponse, status_code=status.HTTP_201_CREATED)
async def create_community(
    community_data: CommunityCreate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    community_crud = get_community_crud()
    
    # Check if community name exists
    # We'd need a method to check by name - for now, we'll search
    existing = await community_crud.search(db, query=community_data.name, limit=1)
    if existing and existing[0].name.lower() == community_data.name.lower():
        raise APIError(
            code="COMMUNITY_EXISTS",
            message=f"Community '{community_data.name}' already exists",
            status_code=status.HTTP_409_CONFLICT,
        )
    
    community = await community_crud.create_with_creator(
        db,
        obj_in=community_data,
        creator_id=uuid.UUID(current_user["id"]),
    )
    
    # Get full community with details
    full_community = await community_crud.get_with_details(
        db, community.id, user_id=uuid.UUID(current_user["id"])
    )
    
    return full_community

# Get community details
@router.get("/{community_id}", response_model=CommunityResponse)
async def get_community(
    community_id: str = Path(...),
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(current_user["id"]) if current_user else None
    
    community_crud = get_community_crud()
    community = await community_crud.get_with_details(db, uuid.UUID(community_id), user_id)
    
    if not community:
        raise NotFoundError("Community", community_id)
    
    return community

# Join a community
@router.post("/{community_id}/join")
async def join_community(
    community_id: UUID = Path(...),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    community_crud = get_community_crud()

    result = await community_crud.join_community(
        db=db,
        community_id=community_id,
        user_id=UUID(current_user["id"]),
    )

    if not result["joined"]:
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Unable to join community"),
        )

    return result

#leave a community
@router.post("/{community_id}/leave")
async def leave_community(
    community_id: UUID = Path(...),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    community_crud = get_community_crud()

    result = await community_crud.leave_community(
        db=db,
        community_id=community_id,
        user_id=UUID(current_user["id"]),
    )

    if not result["left"]:
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Unable to leave community"),
        )

    return result

# Get members of a community
@router.get("/{community_id}/members", response_model=List[CommunityMemberOut])
async def get_community_members(
    community_id: UUID = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
):
    community_crud = get_community_crud()

    community = await community_crud.get(db, community_id)
    if not community:
        raise NotFoundError("Community", str(community_id))

    members = await community_crud.get_members(
        db=db,
        community_id=community_id,
        skip=skip,
        limit=limit,
    )

    return [
        CommunityMemberOut(
            user_id=m.user.id,
            username=m.user.username,
            is_admin=m.is_admin,
            joined_at=m.joined_at,
        )
        for m in members
    ]


# Get posts within a community
@router.get("/{community_id}/posts", response_model=PostListResponse)
async def get_community_posts(
    community_id: str = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # In a real implementation, posts would be tagged with community_id
    # For now, we'll filter by community name in tags
    
    community_crud = get_community_crud()
    community = await community_crud.get(db, uuid.UUID(community_id))

    if not community:
        raise NotFoundError("Community", community_id)

    assert community is not None  # Help type checker narrow the type

    user_id = uuid.UUID(current_user["id"]) if current_user else None

    post_crud = get_post_crud()
    posts = await post_crud.get_multi_filtered(
        db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        query=community.name,  # Search by community name in tags/title
    )

    total = await post_crud.get_count_filtered(
        db,
        query=community.name,
    )

    return {
        "data": posts,
        "pagination": {
            "page": (skip // limit) + 1,
            "limit": limit,
            "total": total,
            "hasNext": skip + limit < total,
            "hasPrev": skip > 0,
        }
    }