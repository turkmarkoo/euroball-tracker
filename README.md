# EuroBall Moves

European basketball transfer news on GitHub Pages. The September 2026 update implements the approved Clear Court (design A) direction with responsive transfer rows, mobile filters, team browsing and a source directory.

## Files

- `index.html`, `styles.css`, `app.mjs`: static, dependency-free UI.
- `data-core.mjs`: normalization, event deduplication and filtering.
- `transfers_all.json`: public records plus preserved `_visited` crawler markers. `count` includes markers; `public_count` excludes them. Rendering always excludes markers and invalid entries.
- `transfers_new.json`: latest reviewed batch.
- `sources.json`: source directory and review coverage notes.
- `data-review.json`: latest source-review date and import log.
- `data-needs-review.json`: quarantined malformed entries, retained for correction.
- `rss.xml`: recent transfer feed.

## Preview and verify

Serve this directory using a static HTTP server (ES modules cannot load through `file://`). For example, run `python -m http.server 8000` and visit `http://localhost:8000`.

Run `node --test data-core.test.mjs` (Node 18+).

## Data policy

Keep direct article URLs, event dates, status and source name. A `verified_at` date means the cited transfer story was checked on that date. It does not mean the whole historical archive was reverified. When only a retrospective report date is available, set `date_basis: "report_date"`; the UI labels it Reported. Unknown origin, position or contract details remain unspecified.

Distinct dates and statuses are separate events. Same-player/destination/status/date duplicates merge source links and retain alias IDs. A confirmed signing can retain its previous rumor in `history`. Team pages show news activity, not guaranteed current rosters.

## Local edits

More → Add a transfer locally or open a player → Edit locally. Changes stay in browser storage and are labeled Local edit. More → Export local changes downloads the edits/additions for review and publication; it does not update GitHub automatically. Existing local edits/additions from the previous interface remain supported.

## Publishing and updates

GitHub Pages serves this repository. The existing Python scripts and manual GitHub Actions workflows remain available. Scheduled scraping is disabled. Reload published data re-downloads the published JSON; it does not search external websites. Source pages may block scraping, so review scraped output before publishing. Update `data-review.json` only after a human/source review, independently of scraper timestamps.

Source sweep on 8 September 2026: 37 additions and one rumor-to-signing update. Nineteen entries use clearly labeled report dates. Coverage spans the 30 listed endpoints plus direct club sources; some endpoints were inaccessible or returned older cached content. This is a targeted backfill, not a claim of exhaustive coverage.
