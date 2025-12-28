# app/models/enums.py
import enum


class PostType(str, enum.Enum):
    OPPORTUNITY = "OPPORTUNITY"
    IDEA = "IDEA"
    LINK = "LINK"
    EVENT = "EVENT"
    CASUAL = "CASUAL"
    MARKETPLACE = "MARKETPLACE"
    LOST_AND_FOUND = "LOST_AND_FOUND"
    NEWS = "NEWS"
    CLUB = "CLUB"
    BOUNTY = "BOUNTY"


class PostStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    SOLD = "SOLD"


class College(str, enum.Enum):
    COE = "COE"
    CST = "CST"
    CMSS = "CMSS"
    CLDS = "CLDS"
    GLOBAL = "GLOBAL"
