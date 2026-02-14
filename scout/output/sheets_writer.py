"""Google Sheets output writer."""

import logging
from typing import List, Optional

from scout.models.person import ScoredPerson
from scout.models.output import OutputRow

logger = logging.getLogger(__name__)


class GoogleSheetsWriter:
    """Write scored people to Google Sheets."""

    def __init__(self, sheet_id: str, credentials_path: Optional[str] = None):
        """
        Initialize Google Sheets writer.

        Args:
            sheet_id: Google Sheet ID
            credentials_path: Path to service account credentials JSON
        """
        self.sheet_id = sheet_id
        self.credentials_path = credentials_path
        self.client = None
        self.rows_written = 0

        try:
            import gspread
            from google.oauth2.service_account import Credentials

            # Set up credentials
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]

            if credentials_path:
                creds = Credentials.from_service_account_file(
                    credentials_path, scopes=scopes
                )
            else:
                # Try default credentials
                creds = Credentials.from_service_account_file(
                    "credentials.json", scopes=scopes
                )

            self.client = gspread.authorize(creds)
            logger.info(f"Initialized Google Sheets writer for sheet {sheet_id}")

        except ImportError:
            logger.error("gspread not installed. Install with: pip install gspread google-auth")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            raise

    def write(self, people: List[ScoredPerson]):
        """
        Write scored people to Google Sheets.

        Args:
            people: List of scored people to write
        """
        if not people:
            logger.info("No people to write")
            return

        try:
            # Open spreadsheet
            sheet = self.client.open_by_key(self.sheet_id)
            worksheet = sheet.get_worksheet(0)  # First sheet

            # Sort by total_score descending
            people_sorted = sorted(people, key=lambda p: p.total_score, reverse=True)

            # Convert to output rows
            output_rows = [OutputRow.from_scored_person(p) for p in people_sorted]

            # Prepare header
            header = [
                "Name",
                "Title",
                "Company",
                "Fit Score",
                "Response Score",
                "Total Score",
                "Fit Reasons",
                "Response Reasons",
                "Source Article",
                "Profile URLs",
                "LinkedIn",
                "Email",
                "School",
                "Role",
                "Seniority",
                "Location",
                "Industries",
                "Discovered Date",
            ]

            # Prepare data rows
            data = []
            for row in output_rows:
                data.append(
                    [
                        row.name,
                        row.title,
                        row.company,
                        row.fit_score,
                        row.response_score,
                        row.total_score,
                        row.fit_reasons,
                        row.response_reasons,
                        row.source_article_url,
                        row.source_profile_urls,
                        row.linkedin_url or "",
                        row.email or "",
                        row.school or "",
                        row.role or "",
                        row.seniority or "",
                        row.location or "",
                        row.industries or "",
                        row.discovered_date,
                    ]
                )

            # Clear existing content and write
            worksheet.clear()
            worksheet.append_row(header)
            worksheet.append_rows(data)

            self.rows_written = len(data)
            logger.info(f"Wrote {self.rows_written} rows to Google Sheets")

        except Exception as e:
            logger.error(f"Failed to write to Google Sheets: {e}")
            raise

    def get_stats(self) -> dict:
        """Get writing statistics."""
        return {
            "sheet_id": self.sheet_id,
            "rows_written": self.rows_written,
        }
