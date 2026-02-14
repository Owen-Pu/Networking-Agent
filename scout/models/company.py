"""Company extraction models."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CompanyMention(BaseModel):
    """LLM output for company extraction from articles."""

    name: str = Field(description="Company name")
    description: Optional[str] = Field(
        default=None, description="Brief description of the company"
    )
    team_page_url: Optional[str] = Field(default=None, description="URL to team/about page")
    mentioned_context: str = Field(
        description="Context in which the company was mentioned (funding, hiring, etc.)"
    )


class CompanyExtractionResult(BaseModel):
    """Container for multiple company extractions."""

    companies: List[CompanyMention] = Field(default_factory=list)


class Company(BaseModel):
    """Company information with source tracking."""

    name: str
    description: Optional[str] = None
    team_page_url: Optional[str] = None
    source_article_url: str
    extracted_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
