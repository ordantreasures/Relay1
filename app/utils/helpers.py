import random
import string
from datetime import datetime
from typing import List, Any, Dict
import uuid


def generate_username(base: str) -> str:
    """Generate a unique username from base."""
    suffix = ''.join(random.choices(string.digits, k=3))
    return f"{base}{suffix}"


def format_datetime(dt: datetime) -> str:
    """Format datetime for display."""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 365:
        return f"{diff.days // 365}y ago"
    elif diff.days > 30:
        return f"{diff.days // 30}mo ago"
    elif diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600}h ago"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60}m ago"
    else:
        return "Just now"


def paginate_response(
    data: List[Any],
    total: int,
    skip: int,
    limit: int,
    base_url: str = "",
    **kwargs,
) -> Dict[str, Any]:
    """Create paginated response."""
    page = (skip // limit) + 1 if limit > 0 else 1
    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    
    response = {
        "data": data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }
    }
    
    # Add next/prev URLs if base_url provided
    if base_url:
        query_params = {k: v for k, v in kwargs.items() if v is not None}
        
        if response["pagination"]["has_next"]:
            next_skip = skip + limit
            query_params["skip"] = next_skip
            query_params["limit"] = limit
            response["pagination"]["next_url"] = f"{base_url}?{_build_query_string(query_params)}"
        
        if response["pagination"]["has_prev"]:
            prev_skip = max(0, skip - limit)
            query_params["skip"] = prev_skip
            query_params["limit"] = limit
            response["pagination"]["prev_url"] = f"{base_url}?{_build_query_string(query_params)}"
    
    return response


def _build_query_string(params: Dict[str, Any]) -> str:
    """Build query string from params."""
    return "&".join([f"{k}={v}" for k, v in params.items()])


def generate_avatar_url(name: str, size: int = 200) -> str:
    """Generate avatar URL from name."""
    name_encoded = name.replace(" ", "+")
    return f"https://ui-avatars.com/api/?name={name_encoded}&background=000&color=fff&size={size}"