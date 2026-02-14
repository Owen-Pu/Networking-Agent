"""Main pipeline orchestration."""

import logging
import time
from typing import List
from tqdm import tqdm

from scout.models.config import ScoutConfig
from scout.models.person import ScoredPerson
from scout.config.settings import get_database_path, get_output_path
from scout.storage.database import DedupeDatabase
from scout.llm.factory import get_llm_provider
from scout.extractors.rss import RSSExtractor
from scout.extractors.article import ArticleExtractor
from scout.extractors.company import CompanyExtractor
from scout.extractors.team import TeamPageExtractor
from scout.extractors.person import PersonVetter
from scout.extractors.article_people import ArticlePeopleExtractor
from scout.extractors.team_url_finder import TeamURLFinder
from scout.scoring.scorer import PersonScorer
from scout.pipeline.filters import DedupeFilter, RelevanceFilter
from scout.output.csv_writer import CSVWriter
from scout.output.sheets_writer import GoogleSheetsWriter

logger = logging.getLogger(__name__)


class ScoutPipeline:
    """Main pipeline for startup outreach scouting."""

    def __init__(self, config: ScoutConfig):
        """
        Initialize pipeline with configuration.

        Args:
            config: Scout configuration
        """
        self.config = config

        # Initialize database
        self.db = DedupeDatabase(get_database_path())

        # Initialize LLM provider
        self.llm = get_llm_provider()

        # Initialize extractors
        self.rss_extractor = RSSExtractor(
            max_items=config.limits.max_articles_per_feed
        )
        self.article_extractor = ArticleExtractor()
        self.company_extractor = CompanyExtractor(
            llm=self.llm, max_companies=config.limits.max_companies_per_article
        )
        self.team_extractor = TeamPageExtractor(llm=self.llm)
        self.person_vetter = PersonVetter(llm=self.llm, preferences=config.preferences)
        self.article_people_extractor = ArticlePeopleExtractor(llm=self.llm)
        self.team_url_finder = TeamURLFinder(llm=self.llm)

        # Initialize filters
        self.dedupe_filter = DedupeFilter(db=self.db)
        self.relevance_filter = RelevanceFilter(
            llm=self.llm, keywords=config.keywords
        )

        # Initialize scorer
        self.scorer = PersonScorer(
            preferences=config.preferences, weights=config.scoring_weights
        )

        # Initialize output writers
        self.csv_writer = CSVWriter(output_path=get_output_path())

        self.sheets_writer = None
        if config.google_sheets:
            try:
                self.sheets_writer = GoogleSheetsWriter(
                    sheet_id=config.google_sheets.sheet_id,
                    credentials_path=config.google_sheets.credentials_path,
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Google Sheets writer: {e}")

        logger.info("Pipeline initialized")

    def _deduplicate_people(self, people):
        """
        Deduplicate people by LinkedIn URL or name.

        Args:
            people: List of PersonExtraction objects

        Returns:
            Deduplicated list of people
        """
        seen = set()
        unique = []

        for person in people:
            # Use LinkedIn URL as primary key if available
            if person.linkedin_url:
                key = person.linkedin_url.lower().strip()
            else:
                # Fallback to name
                key = person.full_name.lower().strip()

            if key not in seen:
                seen.add(key)
                unique.append(person)
            else:
                logger.debug(f"Skipping duplicate: {person.full_name}")

        return unique

    def run(self):
        """Run the complete pipeline."""
        logger.info("=" * 60)
        logger.info("Starting Startup Outreach Scout Pipeline")
        logger.info("=" * 60)

        # Step 1: Fetch RSS feeds
        logger.info("\n[1/7] Fetching RSS feeds...")
        rss_items = self.rss_extractor.fetch_all(self.config.rss_feeds)

        if not rss_items:
            logger.warning("No RSS items fetched. Exiting.")
            return

        # Step 2: Dedupe items
        logger.info("\n[2/7] Filtering for new items...")
        new_items = self.dedupe_filter.filter_new_items(rss_items)

        if not new_items:
            logger.info("No new items to process. Exiting.")
            return

        # Step 3: Extract articles
        logger.info("\n[3/7] Extracting article content...")
        articles = []
        for item in tqdm(new_items, desc="Extracting articles"):
            article = self.article_extractor.extract(item.link, item.title)
            if article:
                articles.append(article)
            time.sleep(0.5)  # Be polite

        # Mark articles as seen
        self.dedupe_filter.mark_items_seen(new_items)

        if not articles:
            logger.warning("No articles extracted. Exiting.")
            return

        # Step 4: Filter for relevance
        logger.info("\n[4/7] Filtering articles for relevance...")
        relevant_articles = []
        for article in tqdm(articles, desc="Checking relevance"):
            if self.relevance_filter.is_relevant(article):
                relevant_articles.append(article)
            time.sleep(0.5)  # Rate limiting

        if not relevant_articles:
            logger.info("No relevant articles found. Exiting.")
            return

        # Step 5: Extract companies and people
        logger.info("\n[5/7] Extracting companies and people...")
        all_people = []

        # Tracking for detailed stats
        stats = {
            "article_people_extracted": 0,
            "team_people_extracted": 0,
            "people_vetted": 0,
            "failed_vetting": 0,
            "failed_response_gate": 0,
            "failed_score_threshold": 0,
        }

        for article in tqdm(relevant_articles, desc="Processing articles"):
            # Extract companies
            companies = self.company_extractor.extract(article)
            time.sleep(0.5)

            for company in companies:
                # Collect all people from multiple sources
                all_company_people = []

                # Tier 1: Extract people directly from article
                article_people = self.article_people_extractor.extract(article, company.name)
                all_company_people.extend(article_people)
                stats["article_people_extracted"] += len(article_people)
                time.sleep(0.5)

                # Tier 2: Extract people from team pages
                team_urls = self.team_url_finder.find_team_urls(company, article)

                for team_url in team_urls:
                    try:
                        team_people = self.team_extractor.extract(team_url, company.name)
                        all_company_people.extend(team_people)
                        stats["team_people_extracted"] += len(team_people)
                        time.sleep(0.5)
                    except Exception as e:
                        logger.debug(f"Failed to extract from {team_url}: {e}")
                        continue

                # Deduplicate people by LinkedIn URL or name+company
                unique_people = self._deduplicate_people(all_company_people)

                # Limit people per company
                unique_people = unique_people[: self.config.limits.max_people_per_company]

                # Vet and score each person
                for person in unique_people:
                    stats["people_vetted"] += 1

                    # Vet person
                    vetting = self.person_vetter.vet(person)
                    time.sleep(0.5)

                    if not vetting:
                        logger.debug(f"Vetting failed for {person.full_name}")
                        stats["failed_vetting"] += 1
                        continue

                    # Check if matches criteria (unless debug mode)
                    if not vetting.matches_criteria and not self.config.debug_keep_nonmatching:
                        logger.debug(f"Person {person.full_name} doesn't match criteria")
                        stats["failed_vetting"] += 1
                        continue

                    # Stage 1: Response Likelihood Gate
                    response_score, response_reasons = self.scorer.calculate_response_score(
                        vetting, company
                    )

                    if response_score < self.config.limits.min_response_threshold:
                        logger.debug(
                            f"Person {person.full_name} failed response threshold: "
                            f"{response_score:.2f} < {self.config.limits.min_response_threshold}"
                        )
                        stats["failed_response_gate"] += 1
                        continue

                    # Stage 2: Fit Scoring (only for candidates who passed Stage 1)
                    scored_person = self.scorer.score_person(
                        extraction=person,
                        vetting=vetting,
                        company=company,
                        article_url=article.url,
                    )

                    # Check minimum total score threshold
                    if scored_person.total_score >= self.config.limits.min_score_threshold:
                        all_people.append(scored_person)
                    else:
                        logger.debug(
                            f"Person {person.full_name} failed score threshold: "
                            f"{scored_person.total_score:.2f} < {self.config.limits.min_score_threshold}"
                        )
                        stats["failed_score_threshold"] += 1

        logger.info(f"\nFound {len(all_people)} qualified candidates")
        logger.info(f"Extraction stats:")
        logger.info(f"  - People from articles: {stats['article_people_extracted']}")
        logger.info(f"  - People from team pages: {stats['team_people_extracted']}")
        logger.info(f"  - Total people vetted: {stats['people_vetted']}")
        logger.info(f"Filtering stats:")
        logger.info(f"  - Failed vetting/criteria: {stats['failed_vetting']}")
        logger.info(f"  - Failed response gate: {stats['failed_response_gate']}")
        logger.info(f"  - Failed score threshold: {stats['failed_score_threshold']}")

        # Step 6: Write output (always, even if empty)
        logger.info("\n[6/7] Writing output...")

        if all_people:
            # Write CSV
            self.csv_writer.write(all_people)
            csv_stats = self.csv_writer.get_stats()
            logger.info(f"CSV output: {csv_stats['output_path']}")
        else:
            logger.warning("No qualified candidates found.")
            logger.warning("Suggestions:")
            logger.warning("  - Lower min_response_threshold or min_score_threshold in config")
            logger.warning("  - Broaden your preferences (schools, roles, industries)")
            logger.warning("  - Enable debug_keep_nonmatching: true to see all extractions")
            logger.warning(f"  - Check logs at data/scout.log for details")
            return

        # Write to Google Sheets if configured
        if self.sheets_writer:
            try:
                self.sheets_writer.write(all_people)
                sheets_stats = self.sheets_writer.get_stats()
                logger.info(f"Google Sheets updated: {sheets_stats['sheet_id']}")
            except Exception as e:
                logger.error(f"Failed to write to Google Sheets: {e}")

        # Step 7: Summary
        logger.info("\n[7/7] Pipeline complete!")
        logger.info("=" * 60)
        logger.info(f"Summary:")
        logger.info(f"  RSS items fetched: {len(rss_items)}")
        logger.info(f"  New items: {len(new_items)}")
        logger.info(f"  Articles extracted: {len(articles)}")
        logger.info(f"  Relevant articles: {len(relevant_articles)}")
        logger.info(f"  Qualified candidates: {len(all_people)}")
        logger.info(f"  Output: {csv_stats['output_path']}")
        logger.info("=" * 60)

        # Database stats
        db_stats = self.db.get_stats()
        logger.info(f"\nDatabase stats: {db_stats}")

    def __del__(self):
        """Cleanup on destruction."""
        if hasattr(self, "db"):
            self.db.close()
