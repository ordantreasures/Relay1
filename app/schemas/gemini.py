from pydantic import BaseModel, Field


class RefinePostRequest(BaseModel):
    text: str = Field(..., min_length=1)
    post_type: str = Field(..., min_length=1)


class RefinePostResponse(BaseModel):
    refined_text: str


class GenerateTitleRequest(BaseModel):
    content: str = Field(..., min_length=1)
    post_type: str = Field(..., min_length=1)


class GenerateTitleResponse(BaseModel):
    title: str
