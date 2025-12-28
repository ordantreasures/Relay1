# schemas/community_member.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class CommunityMemberOut(BaseModel):
    user_id: UUID
    username: str
    is_admin: bool
    joined_at: datetime

    model_config = {
        "from_attributes": True
    }
