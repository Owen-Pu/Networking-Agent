# Startup Outreach Scout

Automated networking candidate discovery from RSS feeds. This tool helps you identify and prioritize people to reach out to for networking based on recent startup news, your preferences, and intelligent scoring.

## Overview

**Startup Outreach Scout** automatically:
1. 📰 Monitors RSS feeds (TechCrunch, VentureBeat, etc.) for startup news
2. 🤖 Uses AI to filter articles for relevance
3. 🏢 Extracts companies and people mentioned in articles
4. 👥 **Two-tier people sourcing**:
   - **Tier 1**: Extracts people directly from article text (founders, executives mentioned)
   - **Tier 2**: Scrapes company team/about pages for additional contacts
5. ✅ Vets candidates against your preferences (schools, roles, industries - all optional)
6. 📊 Scores each person for "fit" and "likely to respond"
7. 📄 Outputs a ranked CSV of the best networking candidates

## Features

- **One-command execution**: `python -m scout run`
- **Configurable preferences**: Target specific schools, roles, industries, seniority levels
- **Intelligent scoring**: Weighted scoring based on your criteria
- **Deduplication**: Never processes the same article twice (SQLite database)
- **Multiple LLM providers**: Supports both OpenAI and Anthropic (Claude)
- **CSV + Google Sheets**: Output to CSV file or directly to Google Sheets
- **Rate limiting**: Polite delays between API calls
- **Progress tracking**: Real-time progress bars and logging

## Installation

### Prerequisites

- Python 3.8 or higher
- API key for Anthropic (Claude) or OpenAI (GPT)

### Setup Steps

1. **Clone or download the repository**

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   ```

   Or install from requirements.txt:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Create a `.env` file in the root directory:
   ```bash
   # Required: Choose your LLM provider
   PROVIDER=anthropic  # or "openai"

   # Anthropic API key (if using Anthropic)
   ANTHROPIC_API_KEY=sk-ant-api03-...

   # OpenAI API key (if using OpenAI)
   OPENAI_API_KEY=sk-...
   ```

5. **Configure your preferences**

   Edit `config.yaml` to set your:
   - RSS feeds to monitor
   - Target schools, roles, industries, seniority levels
   - Scoring weights
   - Processing limits

## Usage

### Weekly Usage

Run this command once per week to discover new networking candidates:

```bash
python -m scout run
```

This will:
- Fetch new articles from your configured RSS feeds
- Filter for relevant startup news
- Extract companies and people
- Score candidates against your preferences
- Write results to `data/output/output.csv`

### Viewing Results

Open `data/output/output.csv` to see your ranked candidates. Columns include:

- **name**: Person's full name
- **title**: Job title
- **company**: Company name
- **total_score**: Combined fit + response score (higher is better)
- **fit_score**: How well they match your preferences
- **response_score**: Estimated likelihood to respond
- **fit_reasons**: Why they're a good match
- **response_reasons**: Factors affecting response likelihood
- **source_article_url**: Original article
- **linkedin_url**: LinkedIn profile (if found)
- **school, role, seniority, location**: Extracted attributes

### Command Options

```bash
python -m scout run --config config.yaml --log-level INFO
```

Options:
- `--config`: Path to config file (default: `config.yaml`)
- `--log-level`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)

## Configuration

Edit `config.yaml` to customize behavior:

### RSS Feeds

```yaml
rss_feeds:
  - url: "https://techcrunch.com/feed/"
    name: "TechCrunch"
  - url: "https://feeds.feedburner.com/venturebeat/SZYF"
    name: "VentureBeat"
```

### Keywords

Articles must contain include keywords and not contain exclude keywords:

```yaml
keywords:
  include:
    - "startup"
    - "funding"
    - "raised"
    - "series"
  exclude:
    - "layoff"
    - "shutdown"
```

### Preferences

Target specific attributes for candidates (**all are optional** - leave empty to match anyone):

```yaml
preferences:
  schools:  # Examples - customize to your targets or leave empty
    - "Vanderbilt University"
    - "UC Berkeley"
    - "Carnegie Mellon"

  roles:  # Examples - customize to your interests
    - "Engineering"
    - "Product"
    - "Design"
    - "Data Science"

  industries:  # Examples - customize to your focus areas
    - "AI/ML"
    - "SaaS"
    - "FinTech"

  seniority_levels:  # Examples - adjust based on who you want to reach
    - "Senior"
    - "Lead"
    - "Staff"
    - "Founder"

  locations:  # Examples - leave empty to match all locations
    - "San Francisco"
    - "New York"
    - "Remote"
```

**Important**: Leave any list empty (e.g., `schools: []`) to match anyone regardless of that attribute. The system works fine with all preferences empty!

### Scoring Weights

Adjust how much each criterion contributes to the fit score:

```yaml
scoring_weights:
  school_match: 2.0      # Higher = more important
  role_match: 1.5
  industry_match: 1.0
  seniority_match: 0.8
  location_match: 0.5
```

### Processing Limits

Control how much data is processed and filtering thresholds:

```yaml
limits:
  max_articles_per_feed: 50       # Max articles from each RSS feed
  max_companies_per_article: 10   # Max companies extracted per article
  max_people_per_company: 20      # Max people extracted per company
  min_response_threshold: 0.3     # Minimum response likelihood (0.0-1.0) - Stage 1 gate
  min_score_threshold: 2.0        # Minimum total score to include in output
```

**Two-Stage Evaluation:**
- **Stage 1 (Response Gate)**: Candidates must first pass `min_response_threshold` (0.0-1.0) based on likelihood to respond. This filters out very senior/busy people early.
- **Stage 2 (Fit Scoring)**: Only candidates who pass Stage 1 are scored for fit against your preferences.

### Output Format

Choose CSV or Google Sheets:

```yaml
output_format: "csv"  # or "sheets"

# Optional: Google Sheets configuration
# google_sheets:
#   sheet_id: "your-google-sheet-id"
#   credentials_path: "path/to/credentials.json"

# Debug mode - keep all candidates even if they don't match criteria
debug_keep_nonmatching: false  # Set to true to see all extractions
```

### Debug Mode

Enable `debug_keep_nonmatching: true` to see all extracted people, even those that don't match your criteria. Useful for:
- Understanding why you're getting 0 candidates
- Seeing what people the system is finding
- Debugging extraction and vetting logic

## Two-Tier People Sourcing

The system uses a robust two-tier approach to find people:

**Tier 1: Article Extraction**
- Directly extracts people mentioned in article text
- Focuses on founders, executives, and team members
- Excludes article authors and journalists
- Works even when no team page URL is available

**Tier 2: Team Page Scraping**
- If article mentions a team page URL, scrapes it directly
- If not, attempts to:
  1. Extract company website from article using LLM
  2. Generate candidate URLs (/team, /about, /leadership, etc.)
  3. Scrape homepage to find team-related navigation links
  4. Extract people from all discovered pages

Both tiers are automatically deduplicated by LinkedIn URL or name before vetting.

## Google Sheets Integration (Optional)

To output directly to Google Sheets:

1. **Create a Google Cloud Project** and enable the Google Sheets API

2. **Create a Service Account** and download the JSON credentials

3. **Share your Google Sheet** with the service account email

4. **Update config.yaml**:
   ```yaml
   output_format: "sheets"
   google_sheets:
     sheet_id: "your-sheet-id-from-url"
     credentials_path: "path/to/service-account-credentials.json"
   ```

5. Run as normal - results will be written to your Google Sheet

## How It Works

### Pipeline Stages

1. **RSS Feed Fetching**: Fetches latest articles from configured feeds
2. **Deduplication**: Filters out previously-seen articles (using SQLite)
3. **Article Extraction**: Downloads article HTML and extracts clean text
4. **Relevance Filtering**: Uses LLM to determine if article is relevant
5. **Company Extraction**: Uses LLM to extract mentioned companies
6. **Team Page Scraping**: Fetches company team/about pages
7. **Person Extraction**: Uses LLM to extract team members from pages
8. **Person Vetting**: Uses LLM to analyze each person against preferences
9. **Scoring**: Calculates fit score (based on preferences) + response score (likelihood to respond)
10. **Output**: Writes ranked results to CSV and/or Google Sheets

### LLM Provider Support

Supports both OpenAI and Anthropic via the `PROVIDER` environment variable:

- **Anthropic (Claude)**: Set `PROVIDER=anthropic` and `ANTHROPIC_API_KEY`
- **OpenAI (GPT)**: Set `PROVIDER=openai` and `OPENAI_API_KEY`

The system uses structured outputs with automatic retry on validation errors.

### Deduplication

All processed article URLs are stored in `data/scout.db` (SQLite). On subsequent runs, articles are skipped if they've been seen before. This prevents reprocessing and wasted API calls.

### Scoring Algorithm

**Two-Stage Evaluation Process:**

**Stage 1: Response Likelihood Gate**
- Response score is computed first (0.0 - 1.0)
- Based on seniority (C-level = lower, senior IC = higher)
- Recent company news (just raised funding = higher)
- Role type (recruiting/BD/sales = higher)
- **If response score < `min_response_threshold`, candidate is excluded immediately**
- Only candidates who pass this gate proceed to Stage 2

**Stage 2: Fit Scoring** (only for candidates who passed Stage 1)
- **Fit Score** = Weighted sum of:
  - School match (e.g., 2.0 points if matches target school)
  - Role match (e.g., 1.5 points if matches target role)
  - Industry match (e.g., 1.0 points per matched industry)
  - Seniority match (e.g., 0.8 points if matches target level)
  - Location match (e.g., 0.5 points if matches target location)

**Total Score** = Fit Score + Response Score

Candidates must pass both:
1. `min_response_threshold` (Stage 1 gate, default 0.3)
2. `min_score_threshold` (Total score threshold, default 2.0)

## Project Structure

```
startup-scout-agent/
├── scout/                      # Main package
│   ├── config/                 # Configuration management
│   ├── llm/                    # LLM provider abstraction
│   ├── models/                 # Pydantic data models
│   ├── extractors/             # Data extraction modules
│   ├── storage/                # SQLite deduplication
│   ├── scoring/                # Scoring logic
│   ├── output/                 # CSV/Sheets writers
│   ├── pipeline/               # Pipeline orchestration
│   └── utils/                  # Utilities and logging
├── data/                       # Runtime data
│   ├── scout.db               # Deduplication database
│   └── output/                # CSV outputs
├── config.yaml                # User configuration
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Package metadata
└── README.md                  # This file
```

## Troubleshooting

### No results found

- Check that your RSS feeds are accessible
- Verify your API key is set correctly
- Lower `min_score_threshold` in config.yaml
- Check logs in `data/scout.log` for errors

### LLM API errors

- Verify your API key is valid and has credits
- Check your internet connection
- Review rate limits for your API tier

### Missing team pages

- Many companies don't have easily-scrapable team pages
- The LLM tries to find team page URLs, but not all articles mention them
- Consider adding direct team page URLs to your feeds

### Google Sheets not working

- Verify service account credentials are correct
- Ensure the sheet is shared with the service account email
- Check that gspread and google-auth are installed

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black scout/
```

### Adding New RSS Feeds

Simply add to the `rss_feeds` list in `config.yaml`:

```yaml
rss_feeds:
  - url: "https://example.com/feed.xml"
    name: "Example Feed"
```

## Limitations

- Relies on articles mentioning team pages or having accessible team information
- LLM extraction accuracy depends on page content quality
- Rate-limited by API quotas (typically 50-60 requests/minute)
- Some companies use JavaScript-heavy sites that may not scrape well

## Future Enhancements

- LinkedIn profile scraping (with authentication)
- Email enrichment via external APIs
- Slack/email notifications for high-score candidates
- Historical tracking of candidate engagement
- A/B testing different outreach approaches

## License

MIT License - feel free to use and modify as needed.

## Support

For issues, questions, or feature requests, please open an issue on the GitHub repository.

---

**Happy networking! 🚀**
