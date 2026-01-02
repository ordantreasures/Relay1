from fastapi import APIRouter, HTTPException
from app.schemas.gemini import (
    RefinePostRequest,
    RefinePostResponse,
    GenerateTitleRequest,
    GenerateTitleResponse,
)
from app.services.gemini_service import gemini_service

router = APIRouter()

# Refine post content endpoint
@router.post("/refine", response_model=RefinePostResponse)
async def refine_post(payload: RefinePostRequest):
    try:
        refined = await gemini_service.refine_post_content(
            text=payload.text,
            post_type=payload.post_type,
        )
        return {"refined_text": refined}

    except Exception:
        raise HTTPException(status_code=500, detail="Post refinement failed")

# Generate post title endpoint
@router.post("/title", response_model=GenerateTitleResponse)
async def generate_title(payload: GenerateTitleRequest):
    try:
        title = await gemini_service.generate_post_title(
            content=payload.content,
            post_type=payload.post_type,
        )
        return {"title": title}

    except Exception:
        raise HTTPException(status_code=500, detail="Title generation failed")
