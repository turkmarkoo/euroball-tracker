EuroBall Moves — Scraper
Automatically scrapes 36 European basketball news sources every 30 minutes and writes structured JSON that the EuroBall Moves tracker reads live.

Files
File	Purpose
scrape.py	Main scraper — fetches all sources, parses articles, writes JSON
transfers_new.json	Only entries found since last run (read by the HTML tracker)
transfers_all.json	Full archive of every entry ever scraped
.github/workflows/scrape.yml	GitHub Actions schedule (every 30 min)
How it works
GitHub Actions triggers scrape.py every 30 minutes
The scraper fetches all 36 sites in the URL database
New articles (not seen before) are written to transfers_new.json
The workflow commits the updated JSON back to the repo
The EuroBall Moves HTML page fetches transfers_new.json on "Fetch Latest"
Setup (one-time)
1. Add this to your existing EB-scrape repo
```bash

Copy scrape.py and the workflow file into your repo
cp scrape.py /path/to/EB-scrape/ cp -r .github /path/to/EB-scrape/ cd /path/to/EB-scrape git add scrape.py .github/ git commit -m "Add EuroBall Moves scraper" git push ```

2. Enable GitHub Actions
Go to your repo → Actions tab → enable workflows if prompted.

3. Connect the HTML tracker to this repo
In euroball-verified-targets.html, the "Fetch Latest" button will read from:

https://raw.githubusercontent.com/blazerculj-max/EB-scrape/main/transfers_new.json

This URL always returns the latest scraped data, no authentication needed (public repo).

4. Test manually
bash python scrape.py

Or trigger from GitHub: Actions → EuroBall Moves Scrape → Run workflow

Parsers
Parser	Sites	Method
nextdata	EuroLeague, EuroCup	Extracts __NEXT_DATA__ JSON from Next.js pages — gets full article list with dates/teasers
aba	ABA Liga (3 pages)	Regex on /news/NNNNN/ link patterns in HTML
sportando	Sportando	Regex on <h2><a href> patterns + date extraction from DD/MM/YYYY text
generic	All other 29 sites	General <h2>/<h3>/<div> article link parser with multilingual status keywords (English, Serbian, Croatian, Polish, Romanian, Greek, Turkish)
Output format (transfers_new.json)
json { "generated_at": "2026-06-19T14:30:00+00:00", "count": 5, "items": [ { "id": "nd-marek-blazevic-rejoins-zalgiri", "player": "Marek Blazevic rejoins Zalgiris after four years away", "pos": "?", "from": "?", "to": "?", "league": "EuroLeague", "status": "signed", "date": "2026-06-19", "summary": "Marek Blazevic rejoins Zalgiris after four years away", "source_name": "EuroLeague Official", "source_url": "https://www.euroleaguebasketball.net/en/euroleague/news/marek-blazevic-rejoins-zalgiris-after-four-years-away/", "_isNew": true } ] }

Note: player, from, to contain the article headline until a more advanced NLP step parses them — the HTML tracker displays the full headline as-is for scraped entries, which is already useful for navigation.

Scheduling
Default schedule: - Every 30 minutes from 06:00–23:00 UTC (peak transfer announcement hours) - Every 2 hours overnight (00:00–06:00 UTC)

To change, edit .github/workflows/scrape.yml → cron expressions.

Extending
To add a new source, add one dict to SOURCES in scrape.py:

python {"name": "New Site Name", "url": "https://example.com/news/", "league": "EuroLeague", "parser": "generic"},

Then push to GitHub — it'll be picked up on the next scheduled run.
