"""Article content extraction."""

import logging
import requests
from datetime import datetime
from typing import Optional
from readability import Document
from bs4 import BeautifulSoup

from scout.models.article import ArticleContent

logger = logging.getLogger(__name__)


class ArticleExtractor:
    """Extract readable content from web articles."""

    def __init__(self, timeout: int = 10):
        """
        Initialize article extractor.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def extract(self, url: str, title: str = "") -> Optional[ArticleContent]:
        """
        Extract article content from URL.

        Args:
            url: Article URL
            title: Article title (from RSS)

        Returns:
            ArticleContent or None if extraction fails
        """
        try:
            logger.debug(f"Extracting article: {url}")

            # Fetch HTML
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            # Ensure proper encoding
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding

            # Extract readable content using readability (requires string, not bytes)
            doc = Document(response.text)
            clean_html = doc.summary()

            # Convert HTML to plain text
            soup = BeautifulSoup(clean_html, "html.parser")
            cleaned_text = soup.get_text(separator="\n", strip=True)

            # Fallback to full HTML text if readability extraction is too short
            if len(cleaned_text) < 200:
                soup_full = BeautifulSoup(response.text, "html.parser")
                # Remove script and style elements
                for script in soup_full(["script", "style"]):
                    script.decompose()
                cleaned_text = soup_full.get_text(separator="\n", strip=True)

            article = ArticleContent(
                url=url,
                title=title or doc.title(),
                text=response.text,
                cleaned_text=cleaned_text,
                extracted_at=datetime.now(),
            )

            logger.debug(f"Extracted {len(cleaned_text)} chars from {url}")
            return article

        except requests.RequestException as e:
            logger.warning(f"Failed to fetch article {url}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Failed to extract article {url}: {e}")
            return None
