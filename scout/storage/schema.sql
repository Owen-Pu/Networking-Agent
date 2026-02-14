-- Database schema for deduplication

CREATE TABLE IF NOT EXISTS seen_urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    item_type TEXT NOT NULL,  -- 'article', 'company', 'person'
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_url ON seen_urls(url);
CREATE INDEX IF NOT EXISTS idx_item_type ON seen_urls(item_type);
CREATE INDEX IF NOT EXISTS idx_first_seen ON seen_urls(first_seen);
