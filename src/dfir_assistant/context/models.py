"""Domain models for organization context."""

from datetime import datetime
from pydantic import BaseModel, Field


class ToolInventory(BaseModel):
    """Organization's forensic tool inventory."""
    
    name: str
    version: str
    notes: str = ""


class OrgContext(BaseModel):
    """Organization-specific context."""
    
    org_name: str
    owner: str = ""
    last_updated: datetime | None = None
    review_cadence_days: int = 30
    tools: list[ToolInventory] = Field(default_factory=list)
    procedures: dict[str, str] = Field(default_factory=dict)
    custom_artifacts: dict[str, str] = Field(default_factory=dict)
