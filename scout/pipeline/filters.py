"""Article filtering logic."""

import logging
from typing import List

from scout.llm.base import BaseLLMProvider
from scout.llm.prompts import relevance_prompt
from scout.models.article import ArticleContent, ArticleRelevance
from scout.models.config import Keywords
from scout.models.rss import RSSItem
from scout.storage.database import DedupeDatabase

logger = logging.getLogger(__name__)


class DedupeFilter:
    """Filter out already-seen items."""

    def __init__(self, db: DedupeDatabase):
        """
        Initialize dedupe filter.

        Args:
            db: Deduplication database
        """
        self.db = db

    def filter_new_items(self, items: List[RSSItem]) -> List[RSSItem]:
        """
        Filter out items that have been seen before.

        Args:
            items: List of RSS items

        Returns:
            List of new (unseen) items
        """
        new_items = []
        for item in items:
            if not self.db.is_seen(item.link):
                new_items.append(item)
            else:
                logger.debug(f"Skipping already-seen item: {item.link}")

        logger.info(f"Filtered to {len(new_items)} new items (from {len(items)} total)")
        return new_items

    def mark_items_seen(self, items: List[RSSItem]):
        """Mark items as seen in database."""
        for item in items:
            self.db.mark_seen(item.link, "article")


class RelevanceFilter:
    """Filter articles for relevance using LLM."""

    def __init__(self, llm: BaseLLMProvider, keywords: Keywords):
        """
        Initialize relevance filter.

        Args:
            llm: LLM provider instance
            keywords: Keyword configuration
        """
        self.llm = llm
        self.keywords = keywords

    def is_relevant(self, article: ArticleContent) -> bool:
        """
        Determine if article is relevant.

        Args:
            article: Article content

        Returns:
            True if article is relevant
        """
        try:
            # Generate prompt
            prompt = relevance_prompt(
                title=article.title,
                text=article.cleaned_text,
                include_keywords=self.keywords.include,
                exclude_keywords=self.keywords.exclude,
            )

            # Call LLM
            result = self.llm.generate_structured(prompt, ArticleRelevance)

            logger.debug(
                f"Relevance check for '{article.title}': "
                f"relevant={result.is_relevant}, confidence={result.confidence:.2f}"
            )

            return result.is_relevant

        except Exception as e:
            logger.error(f"Failed to check relevance for {article.url}: {e}")
            # Default to including on error
            return True

    def filter_articles(self, articles: List[ArticleContent]) -> List[ArticleContent]:
        """
        Filter articles for relevance.

        Args:
            articles: List of articles

        Returns:
            List of relevant articles
        """
        relevant = []
        for article in articles:
            if self.is_relevant(article):
                relevant.append(article)

        logger.info(
            f"Filtered to {len(relevant)} relevant articles (from {len(articles)} total)"
        )
        return relevant
