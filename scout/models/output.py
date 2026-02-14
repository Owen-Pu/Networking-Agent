"""Output data models."""

from typing import Optional, List
from pydantic import BaseModel, Field


class OutputRow(BaseModel):
    """CSV/Sheets output schema."""

    name: str = Field(description="Person's full name")
    title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    fit_score: float = Field(description="Fit score based on preferences")
    response_score: float = Field(description="Estimated likelihood to respond")
    total_score: float = Field(description="Combined total score")
    fit_reasons: str = Field(description="Explanation of why this person is a good fit")
    response_reasons: str = Field(description="Factors affecting response likelihood")
    source_article_url: str = Field(description="Original article URL")
    source_profile_urls: str = Field(description="Comma-separated profile URLs")
    linkedin_url: Optional[str] = Field(default=None, description="LinkedIn profile URL")
    email: Optional[str] = Field(default=None, description="Email address")
    school: Optional[str] = Field(default=None, description="Educational institution")
    role: Optional[str] = Field(default=None, description="Role category")
    seniority: Optional[str] = Field(default=None, description="Seniority level")
    location: Optional[str] = Field(default=None, description="Location")
    industries: Optional[str] = Field(
        default=None, description="Comma-separated industry experience"
    )
    discovered_date: str = Field(description="Date when discovered")

    @classmethod
    def from_scored_person(cls, person) -> "OutputRow":
        """Convert ScoredPerson to OutputRow."""
        return cls(
            name=person.full_name,
            title=person.title or "",
            company=person.company_name,
            fit_score=person.fit_score,
            response_score=person.response_score,
            total_score=person.total_score,
            fit_reasons=person.fit_reasons,
            response_reasons=person.response_reasons,
            source_article_url=person.source_article_url,
            source_profile_urls=", ".join(person.source_profile_urls),
            linkedin_url=person.linkedin_url,
            email=person.email,
            school=person.school,
            role=person.role_category,
            seniority=person.seniority_level,
            location=person.location,
            industries=", ".join(person.industry_experience) if person.industry_experience else None,
            discovered_date=person.extracted_at.strftime("%Y-%m-%d"),
        )
