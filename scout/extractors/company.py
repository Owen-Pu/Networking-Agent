"""Company extraction from articles."""

import logging
from typing import List
from datetime import datetime

from scout.llm.base import BaseLLMProvider
from scout.llm.prompts import company_extraction_prompt
from scout.models.article import ArticleContent
from scout.models.company import Company, CompanyExtractionResult

logger = logging.getLogger(__name__)


class CompanyExtractor:
    """Extract companies from article text using LLM."""

    def __init__(self, llm: BaseLLMProvider, max_companies: int = 10):
        """
        Initialize company extractor.

        Args:
            llm: LLM provider instance
            max_companies: Maximum companies to extract per article
        """
        self.llm = llm
        self.max_companies = max_companies

    def extract(self, article: ArticleContent) -> List[Company]:
        """
        Extract companies from article.

        Args:
            article: Article content

        Returns:
            List of extracted companies
        """
        try:
            logger.debug(f"Extracting companies from: {article.url}")

            # Generate prompt
            prompt = company_extraction_prompt(article.cleaned_text)

            # Call LLM with structured output
            result = self.llm.generate_structured(prompt, CompanyExtractionResult)

            # Convert to Company objects
            companies = []
            for mention in result.companies[: self.max_companies]:
                company = Company(
                    name=mention.name,
                    description=mention.description,
                    team_page_url=mention.team_page_url,
                    source_article_url=article.url,
                    extracted_at=datetime.now(),
                )
                companies.append(company)

            logger.info(f"Extracted {len(companies)} companies from {article.url}")
            return companies

        except Exception as e:
            logger.error(f"Failed to extract companies from {article.url}: {e}")
            return []
