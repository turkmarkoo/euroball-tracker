#!/usr/bin/env python3
"""
scrape.py — EuroBall Moves live transfer scraper
Fetches every site in the URL database, parses transfer articles,
writes transfers_new.json (new entries only) and transfers_all.json (full archive).

Run:  python scrape.py
Output: transfers_new.json, transfers_all.json
"""

import json, re, sys, time, hashlib, os
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# ── URL DATABASE (mirrors the DB array in euroball-verified-targets.html) ────
SOURCES = [
    # EuroLeague / EuroCup  (Next.js __NEXT_DATA__)
    {"name": "EuroLeague Official",       "url": "https://www.euroleaguebasketball.net/euroleague/news/", "league": "EuroLeague",    "parser": "nextdata"},
    {"name": "EuroCup Official",          "url": "https://www.euroleaguebasketball.net/eurocup/news/",    "league": "EuroCup",       "parser": "nextdata"},
    # ABA Liga  (plain HTML, /news/NNNNN/ links)
    {"name": "ABA Liga News (page 1)",    "url": "https://www.aba-liga.com/newslist/News/1/",             "league": "ABA League",    "parser": "aba"},
    {"name": "ABA Liga News (page 2)",    "url": "https://www.aba-liga.com/newslist/News/2/",             "league": "ABA League",    "parser": "aba"},
    {"name": "ABA Liga Clubs News",       "url": "https://www.aba-liga.com/newslist/Clubs/1/",            "league": "ABA League",    "parser": "aba"},
    # BCL
    {"name": "BCL Official News",         "url": "https://www.championsleague.basketball/en/news/",       "league": "BCL",           "parser": "generic"},
    # BBL
    {"name": "BBL basketball-world.news", "url": "https://www.basketball-world.news",                     "league": "BBL",           "parser": "generic"},
    # ACB
    {"name": "ACB Official News",         "url": "https://www.acb.com/es/liga/noticias",                  "league": "ACB",           "parser": "generic"},
    # France
    {"name": "bebasket.fr ELITE",         "url": "https://www.bebasket.fr/ligue/betclic-elite",           "league": "Pro A",         "parser": "generic"},
    {"name": "bebasket.fr Transferts",    "url": "https://www.bebasket.fr/ligue/betclic-elite/tableau-transferts", "league": "Pro A", "parser": "generic"},
    # Italy
    {"name": "Pianeta Basket LBA",        "url": "https://www.pianetabasket.com/legabasket-serie-a/",     "league": "Lega",          "parser": "generic"},
    {"name": "Lega Basket Official",      "url": "https://www.legabasket.it/news",                        "league": "Lega",          "parser": "generic"},
    # Greece
    {"name": "sport24.gr Basket League",  "url": "https://www.sport24.gr/tag/basket-league/",             "league": "GBL",           "parser": "generic"},
    # Turkey
    {"name": "basketbolig.com BSL",       "url": "https://basketbolig.com/kategori/basketbol-super-ligi", "league": "Turkish BSL",   "parser": "generic"},
    {"name": "basketfaul.com.tr BSL",     "url": "https://basketfaul.com.tr/category/turkiye/bsl/",       "league": "Turkish BSL",   "parser": "generic"},
    # Romania
    {"name": "baschetromania.ro",         "url": "https://baschetromania.ro/",                            "league": "Romanian LNB",  "parser": "generic"},
    # Poland
    {"name": "PLK Official News",         "url": "https://plk.pl/aktualnosci",                            "league": "PLK",           "parser": "generic"},
    {"name": "super-basket.pl PLK",       "url": "https://super-basket.pl/plk/",                          "league": "PLK",           "parser": "generic"},
    # Hungary
    {"name": "bball1.hu NB1 Transfers",   "url": "https://bball1.hu/atigazolasi-hirosszefoglalo-2026/",   "league": "Hungarian NB1", "parser": "generic"},
    # Croatia
    {"name": "basketball.hr",             "url": "https://basketball.hr/",                                "league": "Croatian HKL",  "parser": "generic"},
    {"name": "jutarnji.hr Košarka",       "url": "https://www.jutarnji.hr/sportske/kosarka/hrvatska-liga","league": "Croatian HKL",  "parser": "generic"},
    # Lithuania
    {"name": "BasketNews LKL",            "url": "https://www.basketnews.lt/news-248448-basketnews-lkl-vasaros-turgus-atnaujinta-0618.html", "league": "LKL", "parser": "generic"},
    # Israel
    {"name": "basket.co.il",             "url": "https://basket.co.il/archive.asp?typeID=1&lang=en",     "league": "Israeli BSL",   "parser": "generic"},
    # News aggregators
    {"name": "Sportando",                 "url": "https://sportando.basketball/en/",                      "league": "Europe",        "parser": "sportando"},
    {"name": "Eurohoops",                 "url": "https://www.eurohoops.net/en/",                         "league": "Europe",        "parser": "generic"},
    {"name": "TalkBasket",               "url": "https://www.talkbasket.net/transfers",                   "league": "Europe",        "parser": "generic"},
    {"name": "BasketNews.com EL Tracker","url": "https://basketnews.com/news-248207-euroleague-transfer-market-2026-rosters-signings-rumors.html", "league": "EuroLeague", "parser": "generic"},
    {"name": "Gigantes (Spain)",          "url": "https://www.gigantes.com/liga-endesa/",                 "league": "ACB",           "parser": "generic"},
    {"name": "AllStarBasket GBL",        "url": "https://www.allstarbasket.gr/ellada/greek-basketball-league/transfer-market-oi-kiniseis-ton-14-omadon-tis-gbl", "league": "GBL", "parser": "generic"},
    {"name": "RealGM Intl Transactions", "url": "https://basketball.realgm.com/international/transactions", "league": "Europe",     "parser": "generic"},
    {"name": "Eurobasket BNXT",          "url": "https://www.eurobasket.com/BNXT-League/basketball-Transfers.aspx", "league": "BNXT", "parser": "generic"},
    {"name": "Basketball Sphere Transferi","url": "https://basketballsphere.com/evroliga/transferi/",     "league": "EuroLeague",    "parser": "generic"},
    {"name": "Basketball Sphere ABA",    "url": "https://basketballsphere.com/aba-liga/",                 "league": "ABA League",    "parser": "generic"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}

TRANSFER_KW = re.compile(
    r"sign|join|extend|keep|renew|return|stay|land|acqui|depart|exit|left|reload|salut|lascia|firma|rinnov|accordo|biennale|nowy|podpisał|przenosi|zostaje|wraca|trener|verpflichtet|verlängert|wechselt|potpisuje|ostaje|napustio|imzaladı|"
    r"reunit|ink|pen|captur|reel|appoint|part.way|coach|farewell|goodbye|confirm|"
    r"seal|bring|lure|new.deal|swap|trade|ostaje|potpisuje|potpisao|napustio|"
    r"napusta|odlazi|produz|bolster|reinforce|arriv",
    re.I,
)

# Articles matching these patterns are NOT transfers — skip them
SKIP_KW = re.compile(
    r"financial|franchise.deal|recap|preview|interview|suspend|facing.ban|"
    r"faces.fine|award|mvp|all.star|draft.combine|scouting.report|power.rank|"
    r"salary.dispute|legal.dispute|faces.financial|sophomore|benchmark|"
    r"college.season|nba.summer.league(?!.*europ)|g.league.season(?!.*europ)",
    re.I,
)

STATUS_MAP = {
    "extended": re.compile(r"extend|renew|stay|kept|keep|continu|remain|unused|retain|ostaje|produz|nastav", re.I),
    "left":     re.compile(r"depart|left|leav|part.way|exit|releas|napustio|napusta|odlazi|otisao|raskinuo|farewell|goodbye|exits", re.I),
    "rumor":    re.compile(r"report|rumor|expect|close.to|target|link|reportedly|zainteresov|pregovara|blizu|navodno|could|might|mulling|considering", re.I),
}

DATE_RE = re.compile(r"(\d{2})/(\d{2})/(202[0-9])")
ISO_DATE_RE = re.compile(r'"publishDate"\s*:\s*"(\d{4}-\d{2}-\d{2})')
ARCHIVE_FILE = "transfers_all.json"
NEW_FILE = "transfers_new.json"


def fetch(url: str, timeout: int = 15) -> str | None:
    """Fetch URL, return HTML string or None on failure."""
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            enc = resp.headers.get_content_charset() or "utf-8"
            return raw.decode(enc, errors="replace")
    except (URLError, HTTPError, Exception) as e:
        print(f"  ⚠  {url[:60]} — {e}", file=sys.stderr)
        return None


def make_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def infer_status(text: str) -> str:
    for status, pattern in STATUS_MAP.items():
        if pattern.search(text):
            return status
    return "signed"


def extract_date(ctx: str, fallback: str) -> str:
    m = DATE_RE.search(ctx)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    m2 = ISO_DATE_RE.search(ctx)
    if m2:
        return m2.group(1)
    return fallback


# ── PARSERS ──────────────────────────────────────────────────────────────────

def parse_nextdata(html: str, source: dict) -> list[dict]:
    """EuroLeague / EuroCup: extract articles from __NEXT_DATA__ JSON."""
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>([\s\S]*?)</script>', html)
    if not m:
        return []
    try:
        nd = json.loads(m.group(1))
        feed = nd.get("props", {}).get("pageProps", {}).get("feed", {}).get("data", [])
    except json.JSONDecodeError:
        return []

    results = []
    for art in feed:
        title = (art.get("heroMedia") or {}).get("title") or art.get("slug", "")
        if not title or not TRANSFER_KW.search(title) or SKIP_KW.search(title):
            continue
        pub = (art.get("publishDate") or "")[:10] or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        teaser = ((art.get("content") or {}).get("teaser")
                  or (art.get("articleMetadata") or {}).get("description")
                  or title)[:120]
        gen_url = art.get("generatedUrl", "")
        art_url = f"https://www.euroleaguebasketball.net{gen_url}" if gen_url else source["url"]
        results.append({
            "id":          "nd-" + (art.get("slug") or make_id(art_url))[:30],
            "player":      title,
            "pos":         "?",
            "from":        "?",
            "to":          "?",
            "league":      source["league"],
            "status":      infer_status(title),
            "date":        pub,
            "summary":     teaser,
            "source_name": source["name"],
            "source_url":  art_url,
            "_isNew":      True,
        })
    return results


def parse_aba(html: str, source: dict) -> list[dict]:
    """ABA Liga: extract /news/NNNNN/ links from HTML."""
    pattern = re.compile(
        r'href="(https://www\.aba-liga\.com/news/(\d+)/([^"]+))"[^>]*>\s*([^<]{5,120})'
    )
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    results, seen = [], set()
    for m in pattern.finditer(html):
        url, nid, _, raw_title = m.group(1), m.group(2), m.group(3), m.group(4)
        title = re.sub(r"\s+", " ", raw_title).strip()
        if nid in seen or len(title) < 5:
            continue
        seen.add(nid)
        results.append({
            "id":          f"aba-{nid}",
            "player":      title,
            "pos":         "?",
            "from":        "?",
            "to":          "?",
            "league":      source["league"],
            "status":      infer_status(title),
            "date":        today,
            "summary":     title[:120],
            "source_name": source["name"],
            "source_url":  url,
            "_isNew":      True,
        })
    return results


def parse_sportando(html: str, source: dict) -> list[dict]:
    """Sportando: extract <h2><a href="/en/SLUG/">TITLE</a></h2> + DD/MM/YYYY dates."""
    pattern = re.compile(
        r'<h[23][^>]*>\s*<a\s+href="(https://sportando\.basketball/en/([\w-]+)/)"[^>]*>\s*([^<]{5,150})\s*</a>',
        re.I
    )
    skip = {"news","europe","cups","usa","world","official","rumors","category","basketball-transactions",
            "nba-transactions","nba-injuries","padel-review"}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    results, seen = [], set()
    for m in pattern.finditer(html):
        url, slug, raw_title = m.group(1), m.group(2), m.group(3)
        if slug in skip or slug in seen:
            continue
        if SKIP_KW.search(title):
            continue  # non-transfer article
        title = re.sub(r"\s+", " ", raw_title).strip()
        if len(title) < 5:
            continue
        seen.add(slug)
        ctx = html[max(0, m.start()-600):m.start()]
        date = extract_date(ctx, today)
        results.append({
            "id":          f"sp-{slug[:40]}",
            "player":      title,
            "pos":         "?",
            "from":        "?",
            "to":          "?",
            "league":      source["league"],
            "status":      infer_status(title),
            "date":        date,
            "summary":     title[:120],
            "source_name": source["name"],
            "source_url":  url,
            "_isNew":      True,
        })
    return results


def parse_generic(html: str, source: dict) -> list[dict]:
    """Generic WordPress/HTML parser: h2/h3/div article links + Serbian keywords."""
    pattern = re.compile(
        r'<(?:h[23]|div)[^>]*>\s*<a\s+href="(https?://[^"#]+)"[^>]*>\s*([^<]{5,200})\s*</a>',
        re.I
    )
    skip_slugs = {
        "home","news","about","contact","results","stats","teams","players","video",
        "najnovije","evroliga","aba-liga","transferi","kladionica","slotovi",
        "category","page","tag","aktualnosci","noticias","nieuws","novinky",
    }
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    results, seen = [], set()

    for m in pattern.finditer(html):
        url, raw_title = m.group(1), m.group(2)
        title = re.sub(r"\s+", " ", raw_title).strip()
        if len(title) < 5 or len(title) > 200:
            continue
        slug = url.rstrip("/").rsplit("/", 1)[-1][:60]
        if not slug or not "-" in slug:
            continue                         # likely a category page
        if not TRANSFER_KW.search(title) or SKIP_KW.search(title):
            continue                         # not a transfer article
        if slug in seen or slug.lower() in skip_slugs:
            continue
        seen.add(slug)

        ctx_before = html[max(0, m.start()-800):m.start()]
        ctx_after  = html[m.start():m.start()+300]
        date = extract_date(ctx_before + ctx_after, today)

        combined = title + " " + slug
        results.append({
            "id":          f"gen-{slug[:40]}",
            "player":      title,
            "pos":         "?",
            "from":        "?",
            "to":          "?",
            "league":      source["league"],
            "status":      infer_status(combined),
            "date":        date,
            "summary":     title[:120],
            "source_name": source["name"],
            "source_url":  url,
            "_isNew":      True,
        })
    return results


PARSERS = {
    "nextdata": parse_nextdata,
    "aba":      parse_aba,
    "sportando": parse_sportando,
    "generic":  parse_generic,
}


# ── ARCHIVE (deduplication across runs) ──────────────────────────────────────

def load_archive() -> dict[str, dict]:
    if not os.path.exists(ARCHIVE_FILE):
        return {}
    try:
        with open(ARCHIVE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return {item["id"]: item for item in data.get("items", [])}
    except Exception:
        return {}


def save_archive(archive: dict[str, dict]) -> None:
    items = sorted(archive.values(), key=lambda x: x.get("date", ""), reverse=True)
    with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "count": len(items),
            "items": items,
        }, f, ensure_ascii=False, indent=2)


def save_new(new_items: list[dict], archive: dict | None = None) -> None:
    # Always write the last 14 days from archive so Fetch Latest shows
    # content even after all articles are already archived.
    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).strftime("%Y-%m-%d")
    recent = [item for item in (archive or {}).values() if item.get("date", "") >= cutoff]
    merged = {item["id"]: item for item in recent}
    merged.update({item["id"]: item for item in new_items})
    items = sorted(merged.values(), key=lambda x: x.get("date", ""), reverse=True)
    with open(NEW_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "count": len(items),
            "items": items,
        }, f, ensure_ascii=False, indent=2)


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print(f"EuroBall Moves Scraper — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Scraping {len(SOURCES)} sources…\n")

    archive = load_archive()
    new_items = []
    total_found = 0

    for i, source in enumerate(SOURCES, 1):
        print(f"[{i:02d}/{len(SOURCES)}] {source['name'][:50]}")
        html = fetch(source["url"])
        if not html:
            print("         → fetch failed, skipping")
            continue

        parser_fn = PARSERS.get(source["parser"], parse_generic)
        items = parser_fn(html, source)
        print(f"         → {len(items)} articles parsed")

        added = 0
        for item in items:
            if item["id"] not in archive:
                archive[item["id"]] = item
                new_items.append(item)
                added += 1

        if added:
            print(f"         ✓ {added} new")
        total_found += added
        time.sleep(0.5)   # be polite between requests

    print(f"\n{'='*50}")
    print(f"Total new: {total_found} | Archive size: {len(archive)}")

    save_archive(archive)
    save_new(new_items, archive)
    print(f"✓ Written {NEW_FILE} ({len(new_items)} items)")
    print(f"✓ Written {ARCHIVE_FILE} ({len(archive)} items total)")


if __name__ == "__main__":
    main()
