"""Team page extraction."""

import logging
import requests
from typing import List
from bs4 import BeautifulSoup

from scout.llm.base import BaseLLMProvider
from scout.llm.prompts import person_extraction_prompt
from scout.models.person import PersonExtraction, PersonExtractionResult

logger = logging.getLogger(__name__)


class TeamPageExtractor:
    """Extract team members from company team/about pages."""

    def __init__(self, llm: BaseLLMProvider, timeout: int = 10):
        """
        Initialize team page extractor.

        Args:
            llm: LLM provider instance
            timeout: Request timeout in seconds
        """
        self.llm = llm
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def extract(self, url: str, company_name: str) -> List[PersonExtraction]:
        """
        Extract team members from team page.

        Args:
            url: Team page URL
            company_name: Company name

        Returns:
            List of extracted people
        """
        try:
            logger.debug(f"Extracting team from: {url}")

            # Fetch page HTML
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            # Parse HTML and extract text
            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text content
            text = soup.get_text(separator="\n", strip=True)

            # Limit text size for LLM
            text = text[:8000]

            # Generate prompt
            prompt = person_extraction_prompt(text, company_name)

            # Call LLM with structured output
            result = self.llm.generate_structured(prompt, PersonExtractionResult)

            logger.info(f"Extracted {len(result.people)} people from {url}")
            return result.people

        except requests.RequestException as e:
            logger.warning(f"Failed to fetch team page {url}: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to extract team from {url}: {e}")
            return []
