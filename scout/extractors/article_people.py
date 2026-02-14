"""Extract people directly from article text."""

import logging
from typing import List

from scout.llm.base import BaseLLMProvider
from scout.models.person import PersonExtraction, PersonExtractionResult
from scout.models.article import ArticleContent

logger = logging.getLogger(__name__)


def article_people_extraction_prompt(article_title: str, article_text: str, company_name: str) -> str:
    """Generate prompt for extracting people from article text."""
    return f"""Extract people associated with the company mentioned in this article.

Article Title: {article_title}

Article Text (first 5000 chars):
{article_text[:5000]}

Company: {company_name}

Extract people who are:
- Founders, co-founders, executives, or team members of {company_name}
- Mentioned in context of hiring, joining the team, or leadership roles
- Contact persons for the company

DO NOT extract:
- Article authors or reporters
- Journalists or press contacts
- People quoted from other companies
- Investors or board members (unless they're also executives)

For each person found, provide:
- full_name: Their full name
- title: Their job title or role at {company_name}
- linkedin_url: LinkedIn profile URL if mentioned
- email: Email address if mentioned
- bio: Brief context about them from the article

Return as JSON with a "people" array containing all qualifying people.
If no qualifying people are found, return an empty array.
"""


class ArticlePeopleExtractor:
    """Extract people directly from article text."""

    def __init__(self, llm: BaseLLMProvider):
        """
        Initialize article people extractor.

        Args:
            llm: LLM provider instance
        """
        self.llm = llm

    def extract(self, article: ArticleContent, company_name: str) -> List[PersonExtraction]:
        """
        Extract people associated with a company from article text.

        Args:
            article: Article content
            company_name: Name of the company to extract people for

        Returns:
            List of extracted people
        """
        try:
            logger.debug(f"Extracting people for {company_name} from article: {article.url}")

            # Generate prompt
            prompt = article_people_extraction_prompt(
                article_title=article.title,
                article_text=article.cleaned_text,
                company_name=company_name,
            )

            # Call LLM with structured output
            result = self.llm.generate_structured(prompt, PersonExtractionResult)

            logger.info(f"Extracted {len(result.people)} people for {company_name} from article")
            return result.people

        except Exception as e:
            logger.error(f"Failed to extract people from article {article.url}: {e}")
            return []
