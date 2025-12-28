from .auth import router as auth_router
from .posts import router as posts_router
from .users import router as users_router
from .communities import router as communities_router
from .notifications import router as notifications_router

__all__ = ["auth_router", "posts_router", "users_router", "communities_router", "notifications_router"]