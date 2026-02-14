"""CSV output writer."""

import logging
import csv
from pathlib import Path
from typing import List

from scout.models.person import ScoredPerson
from scout.models.output import OutputRow

logger = logging.getLogger(__name__)


class CSVWriter:
    """Write scored people to CSV file."""

    def __init__(self, output_path: str):
        """
        Initialize CSV writer.

        Args:
            output_path: Path to output CSV file
        """
        self.output_path = output_path
        self.fieldnames = [
            "name",
            "title",
            "company",
            "fit_score",
            "response_score",
            "total_score",
            "fit_reasons",
            "response_reasons",
            "source_article_url",
            "source_profile_urls",
            "linkedin_url",
            "email",
            "school",
            "role",
            "seniority",
            "location",
            "industries",
            "discovered_date",
        ]
        self.rows_written = 0

    def write(self, people: List[ScoredPerson]):
        """
        Write scored people to CSV.

        Args:
            people: List of scored people to write
        """
        if not people:
            logger.info("No people to write")
            return

        # Sort by total_score descending
        people_sorted = sorted(people, key=lambda p: p.total_score, reverse=True)

        # Convert to output rows
        output_rows = [OutputRow.from_scored_person(p) for p in people_sorted]

        # Ensure output directory exists
        Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)

        # Write to CSV
        try:
            with open(self.output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()

                for row in output_rows:
                    writer.writerow(row.model_dump())
                    self.rows_written += 1

            logger.info(f"Wrote {self.rows_written} rows to {self.output_path}")

        except Exception as e:
            logger.error(f"Failed to write CSV: {e}")
            raise

    def get_stats(self) -> dict:
        """Get writing statistics."""
        return {
            "output_path": self.output_path,
            "rows_written": self.rows_written,
        }
