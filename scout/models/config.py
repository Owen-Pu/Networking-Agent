"""Configuration data models."""

from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class RSSFeed(BaseModel):
    """RSS feed configuration."""

    url: str
    name: str


class Keywords(BaseModel):
    """Keyword filtering configuration."""

    include: List[str] = Field(default_factory=list)
    exclude: List[str] = Field(default_factory=list)


class Preferences(BaseModel):
    """User networking preferences."""

    schools: List[str] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=list)
    industries: List[str] = Field(default_factory=list)
    seniority_levels: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)


class ScoringWeights(BaseModel):
    """Weights for scoring algorithm."""

    school_match: float = 1.0
    role_match: float = 1.0
    industry_match: float = 1.0
    seniority_match: float = 0.5
    location_match: float = 0.3


class Limits(BaseModel):
    """Processing limits configuration."""

    max_articles_per_feed: int = 50
    max_companies_per_article: int = 10
    max_people_per_company: int = 20
    min_response_threshold: float = 0.3
    min_score_threshold: float = 0.5


class GoogleSheetsConfig(BaseModel):
    """Google Sheets configuration."""

    sheet_id: str
    credentials_path: Optional[str] = None


class ScoutConfig(BaseModel):
    """Main configuration model."""

    rss_feeds: List[RSSFeed]
    keywords: Keywords
    preferences: Preferences
    scoring_weights: ScoringWeights = Field(default_factory=ScoringWeights)
    limits: Limits = Field(default_factory=Limits)
    output_format: str = "csv"
    google_sheets: Optional[GoogleSheetsConfig] = None
    debug_keep_nonmatching: bool = False
