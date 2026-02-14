"""RSS feed extraction."""

import logging
import feedparser
from typing import List
from datetime import datetime
from dateutil import parser as date_parser

from scout.models.rss import RSSItem
from scout.models.config import RSSFeed

logger = logging.getLogger(__name__)


class RSSExtractor:
    """Extract items from RSS feeds."""

    def __init__(self, max_items: int = 50):
        """
        Initialize RSS extractor.

        Args:
            max_items: Maximum items to extract per feed
        """
        self.max_items = max_items

    def fetch_feed(self, feed: RSSFeed) -> List[RSSItem]:
        """
        Fetch and parse RSS feed.

        Args:
            feed: RSS feed configuration

        Returns:
            List of RSS items
        """
        try:
            logger.info(f"Fetching RSS feed: {feed.name} ({feed.url})")
            parsed = feedparser.parse(feed.url)

            if parsed.bozo:
                logger.warning(f"Feed parsing had issues: {feed.name}")

            items = []
            for entry in parsed.entries[: self.max_items]:
                try:
                    # Parse published date
                    published = None
                    if hasattr(entry, "published"):
                        try:
                            published = date_parser.parse(entry.published)
                        except:
                            pass

                    # Get unique identifier
                    guid = entry.get("id") or entry.get("link") or entry.get("title", "")

                    item = RSSItem(
                        title=entry.get("title", "No title"),
                        link=entry.get("link", ""),
                        published=published,
                        description=entry.get("description") or entry.get("summary"),
                        feed_name=feed.name,
                        guid=guid,
                    )
                    items.append(item)
                except Exception as e:
                    logger.warning(f"Failed to parse entry from {feed.name}: {e}")
                    continue

            logger.info(f"Extracted {len(items)} items from {feed.name}")
            return items

        except Exception as e:
            logger.error(f"Failed to fetch feed {feed.name}: {e}")
            return []

    def fetch_all(self, feeds: List[RSSFeed]) -> List[RSSItem]:
        """
        Fetch all RSS feeds.

        Args:
            feeds: List of RSS feed configurations

        Returns:
            Combined list of all RSS items
        """
        all_items = []
        for feed in feeds:
            items = self.fetch_feed(feed)
            all_items.extend(items)

        logger.info(f"Total items fetched: {len(all_items)}")
        return all_items
