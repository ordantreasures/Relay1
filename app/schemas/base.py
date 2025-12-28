# schemas/base.py
from pydantic import BaseModel, Field, field_validator
from uuid import UUID

class BaseSchema(BaseModel):
    """Base schema with UUID handling"""
    
    @field_validator('*', mode='before')
    @classmethod
    def convert_uuid_to_string(cls, v, info):
        # Convert UUID objects to strings
        if isinstance(v, UUID):
            return str(v)
        return v