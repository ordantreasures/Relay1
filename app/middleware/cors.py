from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ..config import settings


def setup_cors(app: FastAPI):
    """Configure CORS middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "X-Requested-With",
            "X-CSRF-Token",
        ],
        expose_headers=["Content-Length", "X-Total-Count"],
        max_age=600,  # 10 minutes
    )