"""Person extraction, vetting, and scoring models."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PersonExtraction(BaseModel):
    """LLM output for person extraction from team pages."""

    full_name: str = Field(description="Full name of the person")
    title: Optional[str] = Field(default=None, description="Job title")
    linkedin_url: Optional[str] = Field(default=None, description="LinkedIn profile URL")
    email: Optional[str] = Field(default=None, description="Email address if available")
    bio: Optional[str] = Field(default=None, description="Brief bio or description")


class PersonExtractionResult(BaseModel):
    """Container for multiple person extractions."""

    people: List[PersonExtraction] = Field(default_factory=list)


class PersonVetting(BaseModel):
    """LLM output for vetting person against preferences."""

    school: Optional[str] = Field(default=None, description="Educational institution")
    role_category: Optional[str] = Field(
        default=None, description="Role category (Engineering, Product, etc.)"
    )
    seniority_level: Optional[str] = Field(
        default=None, description="Seniority level (Senior, Lead, etc.)"
    )
    location: Optional[str] = Field(default=None, description="Location")
    industry_experience: List[str] = Field(
        default_factory=list, description="List of relevant industries"
    )
    matches_criteria: bool = Field(
        description="Whether person matches target preferences"
    )
    reasoning: str = Field(description="Explanation of the vetting decision")


class ScoredPerson(BaseModel):
    """Final person with complete information and score."""

    full_name: str
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    company_name: str
    company_url: Optional[str] = None
    school: Optional[str] = None
    role_category: Optional[str] = None
    seniority_level: Optional[str] = None
    location: Optional[str] = None
    industry_experience: List[str] = Field(default_factory=list)
    fit_score: float = Field(description="Score based on matching criteria")
    response_score: float = Field(
        description="Score estimating likelihood to respond"
    )
    total_score: float = Field(description="Combined score")
    fit_reasons: str = Field(description="Explanation of fit score")
    response_reasons: str = Field(description="Explanation of response score")
    source_article_url: str
    source_profile_urls: List[str] = Field(default_factory=list)
    extracted_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
