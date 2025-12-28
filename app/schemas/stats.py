# app/schemas/stats.py
from pydantic import BaseModel

class PostStats(BaseModel):
    views: int
    comments: int
    upvotes: int

    model_config = {"from_attributes": True}
