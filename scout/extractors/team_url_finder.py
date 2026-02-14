"""Find team/about page URLs for companies."""

import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from scout.models.company import Company
from scout.models.article import ArticleContent
from scout.llm.base import BaseLLMProvider
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CompanyWebsite(BaseModel):
    """LLM output for company website extraction."""
    website_url: Optional[str] = None
    confidence: float = 0.0


def website_extraction_prompt(company_name: str, article_text: str) -> str:
    """Generate prompt for extracting company website from article."""
    return f"""Extract the website URL for {company_name} from this article text.

Article text (first 3000 chars):
{article_text[:3000]}

Company: {company_name}

Find the main website URL for this company. Look for:
- Direct mentions of their website (e.g., "visit example.com")
- URLs in the article text
- Domain names associated with the company

Return as JSON:
- website_url: The main website URL (e.g., "https://example.com") or null if not found
- confidence: Your confidence (0.0-1.0) in this URL being correct

If you cannot find a website URL, return null for website_url.
"""


class TeamURLFinder:
    """Find team/about page URLs for companies."""

    def __init__(self, llm: BaseLLMProvider, timeout: int = 5):
        """
        Initialize team URL finder.

        Args:
            llm: LLM provider for website extraction
            timeout: Request timeout in seconds
        """
        self.llm = llm
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def _infer_website_from_name(self, company_name: str) -> Optional[str]:
        """
        Simple heuristic to infer website from company name.
        Only use for very clear cases.
        """
        # Clean company name
        name = company_name.lower().strip()

        # Remove common suffixes
        for suffix in [" inc", " inc.", " llc", " ltd", " corp", " corporation"]:
            if name.endswith(suffix):
                name = name[:-len(suffix)].strip()

        # Remove spaces and special chars
        domain = name.replace(" ", "").replace("-", "").replace("_", "")

        # Only return if it's a simple, short name (likely to be correct)
        if len(domain) <= 20 and domain.isalnum():
            return f"https://{domain}.com"

        return None

    def _extract_website_from_article(self, company_name: str, article: ArticleContent) -> Optional[str]:
        """
        Use LLM to extract company website from article text.
        """
        try:
            prompt = website_extraction_prompt(company_name, article.cleaned_text)
            result = self.llm.generate_structured(prompt, CompanyWebsite)

            if result.website_url and result.confidence > 0.5:
                logger.debug(f"Extracted website for {company_name}: {result.website_url}")
                return result.website_url
        except Exception as e:
            logger.debug(f"Failed to extract website from article: {e}")

        return None

    def _generate_candidate_urls(self, base_url: str) -> List[str]:
        """
        Generate candidate team/about page URLs from base website.
        """
        # Parse base URL
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        # Common team page paths
        paths = [
            "/team",
            "/about",
            "/about-us",
            "/company",
            "/leadership",
            "/people",
            "/our-team",
            "/careers",
            "/about/team",
        ]

        return [urljoin(base, path) for path in paths]

    def _scrape_homepage_for_team_links(self, website_url: str) -> List[str]:
        """
        Scrape homepage to find team/about links in navigation.
        """
        team_urls = []

        try:
            response = requests.get(website_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Find links with team-related keywords
            keywords = ["team", "about", "leadership", "people", "company", "our-team"]

            for link in soup.find_all("a", href=True):
                href = link.get("href", "").lower()
                text = link.get_text(strip=True).lower()

                # Check if link or text contains team keywords
                if any(kw in href or kw in text for kw in keywords):
                    full_url = urljoin(website_url, link["href"])
                    if full_url not in team_urls:
                        team_urls.append(full_url)

            logger.debug(f"Found {len(team_urls)} team-related links on {website_url}")

        except Exception as e:
            logger.debug(f"Failed to scrape homepage {website_url}: {e}")

        return team_urls

    def find_team_urls(self, company: Company, article: ArticleContent) -> List[str]:
        """
        Find candidate team page URLs for a company.

        Args:
            company: Company object
            article: Source article

        Returns:
            List of candidate team page URLs to try
        """
        candidate_urls = []

        # Tier 1: Use existing team_page_url if available
        if company.team_page_url:
            logger.debug(f"Using existing team_page_url for {company.name}")
            candidate_urls.append(company.team_page_url)
            return candidate_urls

        # Tier 2: Try to extract website from article
        website_url = self._extract_website_from_article(company.name, article)

        # Tier 3: Fallback to simple heuristic (only for clear cases)
        if not website_url:
            website_url = self._infer_website_from_name(company.name)
            if website_url:
                logger.debug(f"Inferred website for {company.name}: {website_url}")

        if not website_url:
            logger.debug(f"Could not determine website for {company.name}")
            return []

        # Generate candidate URLs
        candidate_urls.extend(self._generate_candidate_urls(website_url))

        # Try to scrape homepage for team links
        homepage_links = self._scrape_homepage_for_team_links(website_url)
        candidate_urls.extend(homepage_links)

        # Deduplicate while preserving order
        seen = set()
        unique_urls = []
        for url in candidate_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        logger.info(f"Found {len(unique_urls)} candidate team URLs for {company.name}")
        return unique_urls[:5]  # Limit to top 5 to avoid too many requests
