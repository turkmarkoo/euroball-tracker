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



# Club name canonicalization
CLUB_ALIASES = {
    "varese": "Pallacanestro Varese", "openjobmetis varese": "Pallacanestro Varese",
    "olimpia milano": "Olimpia Milano", "armani olimpia milano": "Olimpia Milano",
    "ea7 olimpia milano": "Olimpia Milano", "armani milan": "Olimpia Milano",
    "virtus": "Virtus Bologna", "virtus segafredo bologna": "Virtus Bologna",
    "aquila trento": "Dolomiti Energia Trento", "dolomiti energia trentino": "Dolomiti Energia Trento",
    "guerri napoli": "Napoli Basket", "napolibasket": "Napoli Basket",
    "scaligera verona": "Tezenis Verona", "scaligera basket verona": "Tezenis Verona",
    "pallacanestro reggiana": "UNA Hotels Reggio Emilia", "reggio emilia": "UNA Hotels Reggio Emilia",
    "nutribullet treviso": "NutriBullet Treviso Basket", "treviso basket": "NutriBullet Treviso Basket",
    "dinamo sassari": "Banco di Sardegna Sassari", "sassari": "Banco di Sardegna Sassari",
    "barca basket": "FC Barcelona", "real madrid baloncesto": "Real Madrid",
    "saski baskonia": "Baskonia", "td systems baskonia": "Baskonia",
    "crvena zvezda": "Crvena zvezda Meridianbet", "red star belgrade": "Crvena zvezda Meridianbet", "red star": "Crvena zvezda Meridianbet",
    "partizan": "Partizan Mozzart Bet Belgrade", "partizan belgrade": "Partizan Mozzart Bet Belgrade",
    "u-bt cluj-napoca": "UBT Cluj-Napoca", "u-banca transilvania": "UBT Cluj-Napoca", "u cluj": "UBT Cluj-Napoca",
    "budocnost": "Budćnost Voli", "buducnost": "Budćnost Voli",
    "olympiacos pireo": "Olympiacos Piraeus", "olympiacos bc": "Olympiacos Piraeus", "olympiacos": "Olympiacos Piraeus",
    "panathinaikos aktor": "Panathinaikos Athens", "panathinaikos": "Panathinaikos Athens",
    "fenerbahce": "Fenerbahce Beko Istanbul", "fenerbahce beko": "Fenerbahce Beko Istanbul",
    "efes": "Anadolu Efes",
    "maccabi tel aviv": "Maccabi Rapyd Tel Aviv", "maccabi": "Maccabi Rapyd Tel Aviv",
    "zalgiris": "Žalgiris Kaunas", "as monaco basket": "AS Monaco",
}

def normalize_club(name):
    if not name or name in ("?", "Free Agent"):
        return name
    return CLUB_ALIASES.get(name.lower().strip(), name)

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


# ── AI WEB SEARCH ───────────────────────────────────────────────────────────

def ai_web_search_transfers(api_key: str) -> list[dict]:
    """Use Anthropic web_search to find recent European basketball transfers.
    Runs 6 targeted searches — one per official league/site group — so
    official announcements on euroleaguebasketball.net, aba-liga.com,
    bnxtleague.com, etc. are never missed."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    SEARCH_TARGETS = [
        ("EuroLeague/EuroCup Official",
         "Search site:euroleaguebasketball.net for player signings, transfers and "
         "departures announced in the past 7 days. Cover both EuroLeague and EuroCup."),
        ("ABA League Official",
         "Search site:aba-liga.com for player signings, transfers and departures "
         "announced in the past 7 days."),
        ("BNXT League Official",
         "Search for BNXT League basketball player signings and transfers announced in "
         "the past 7 days. The BNXT League covers Belgium and the Netherlands. "
         "Search: site:bnxtleague.com signings OR transfers. Also search BeBasket.fr "
         "and basketbal.nl for BNXT transfer news. Look for club announcements from "
         "teams like Donar Groningen, Heroes Den Bosch, ZZ Leiden, Spirou Basket, "
         "Leuven Bears, Okapi Aalst, Limburg United, CB Liège, Filou Oostende."),
        ("ACB / Lega Basket / BSL",
         "Search acb.com, legabasket.it and bsl.com.tr for player signings, transfers "
         "and departures announced in the past 7 days."),
        ("Sportando / Eurohoops / TalkBasket",
         "Search sportando.basketball, eurohoops.net and talkbasket.net for European "
         "basketball player transfers and signings from the past 7 days."),
        ("Other European leagues",
         "Search for player transfers and signings in the past 7 days across: "
         "LKL (Lithuania, basketnews.com), PLK (Poland, plk.pl), BCL Basketball "
         "Champions League, Greek Basket League (sport24.gr), Israeli BSL, "
         "Romanian LNB (baschetromania.ro), Hungarian NB1, Croatian HKL."),
    ]

    OUTPUT_SCHEMA = (
        "Return a JSON array. Each element: "
        '{"player":"Full Name","pos":"PG|SG|SF|PF|C|coach|?",'
        '"from":"Previous club or Free Agent or ?","to":"New club or Free Agent or ?",'
        '"status":"signed|rumor|left|extended",'
        '"league":"EuroLeague|EuroCup|ACB|ABA League|Lega Basket|BSL|BNXT|LKL|BCL|?","date":"YYYY-MM-DD",'
        '"source_url":"https://...","source_name":"Site Name","contract":"1 year or 2+1 or null","birth_year":"YYYY integer or null"} '
        "Rules: real player/coach names only; YYYY-MM-DD dates; no duplicates; "
        "return ONLY the JSON array, no markdown, no explanation."
    )

    all_results: list[dict] = []
    seen_keys: set[str] = set()

    for label, instruction in SEARCH_TARGETS:
        prompt = (
            f"Today is {today}.\n\n"
            f"{instruction}\n\n"
            f"{OUTPUT_SCHEMA}"
        )
        body = json.dumps({
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 4000,
            "tools": [{"type": "web_search_20250305", "name": "web_search"}],
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        req = Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        try:
            with urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
                texts = [c["text"] for c in result.get("content", []) if c.get("type") == "text"]
                raw = " ".join(texts).strip()
                if not raw:
                    print(f"  [{label}] no text response")
                    continue
                if "```" in raw:
                    raw = raw.split("```")[1].lstrip("json").strip()
                start, end = raw.find("["), raw.rfind("]") + 1
                if start < 0 or end <= start:
                    print(f"  [{label}] no JSON array found")
                    continue
                batch = json.loads(raw[start:end])
                added = 0
                for item in batch:
                    p = item.get("player", "").strip()
                    t = item.get("to", "").strip()
                    dt = item.get("date", "")
                    key = f"{p.lower()}-{t.lower()}-{dt}"
                    if p and p != "?" and key not in seen_keys:
                        seen_keys.add(key)
                        all_results.append(item)
                        added += 1
                print(f"  [{label}] {added} transfers found")
        except Exception as e:
            print(f"  [{label}] error: {e}")
        time.sleep(1)

    print(f"  Total from AI web search: {len(all_results)}")
    return all_results
# ── AI ENRICHMENT ───────────────────────────────────────────────────────────

def ai_extract(headline: str, url: str, api_key: str) -> dict:
    """Call Claude Haiku to extract structured transfer data from an article headline."""
    prompt = (
        "Extract European basketball transfer data from this headline.\n"
        "Return ONLY a JSON object with exactly these keys:\n"
        "  player: full player name (or coach name), or \"?\"\n"
        "  pos: PG | SG | SF | PF | C | coach | \"?\"\n"
        "  from: club leaving, or \"Free Agent\", or \"?\"\n"
        "  to: club joining, or \"Free Agent\", or \"?\"\n"
        "  status: signed | rumor | left | extended | \"?\"\n"
        "  league: EuroLeague | EuroCup | ACB | ABA League | Lega Basket | "
        "BSL | BCL | LKL | or other European league, or \"?\"\n\n"
        f"Headline: {headline}\nURL: {url}\n\n"
        "  contract: e.g. 1 year or 2+1 or 3 years or null if not mentioned\n"
        "  birth_year: YYYY integer or null (if age X mentioned, use current year minus X)\n"
        "Return only the JSON object — no markdown, no explanation."
    )
    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 150,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    try:
        with urlopen(req, timeout=15) as resp:
            raw = json.loads(resp.read())["content"][0]["text"].strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1].lstrip("json").strip()
            data = json.loads(raw)
            if data.get("player", "?") not in ("?", "", None):
                return {k: v for k, v in data.items() if v and v not in ("?", "")}
    except Exception:
        pass
    return {}


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
    print(f"Total new from scraper: {total_found} | Archive size: {len(archive)}")

    # ── AI web_search: find transfers Anthropic-side (bypasses GitHub Actions IP blocks)
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        print("\nRunning AI web search for recent transfers…")
        ai_items = ai_web_search_transfers(api_key)
        print(f"  AI found {len(ai_items)} transfer entries")
        ai_added = 0
        for item in ai_items:
            if not item.get("player") or item["player"] == "?":
                continue
            id_key = f"{item.get('player','').lower().strip()}-{item.get('to','').lower().strip()}-{item.get('date','')}"
            item["id"] = "ai-" + hashlib.md5(id_key.encode()).hexdigest()[:12]
            if item["id"] not in archive:
                archive[item["id"]] = item
                new_items.append(item)
                ai_added += 1
                total_found += 1
        print(f"  → {ai_added} new AI-discovered transfers added to archive")

    # ── AI Enrichment ────────────────────────────────────────────────────────
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if new_items and api_key:
        need_enrich = [it for it in new_items
                       if it.get("pos") == "?" and it.get("from") == "?" and it.get("to") == "?"]
        if need_enrich:
            print(f"\nEnriching {len(need_enrich)} new items with Claude Haiku…")
            enriched_count = 0
            for item in need_enrich:
                result = ai_extract(item.get("player", ""), item.get("source_url", ""), api_key)
                if result:
                    item.update(result)
                    archive[item["id"]].update(result)
                    item["from"] = normalize_club(item.get("from") or "?")
                    item["to"]   = normalize_club(item.get("to") or "?")
                    archive[item["id"]]["from"] = item["from"]
                    archive[item["id"]]["to"]   = item["to"]
                    enriched_count += 1
                time.sleep(0.3)
            print(f"  → {enriched_count}/{len(need_enrich)} items enriched")

    save_archive(archive)
    save_new(new_items, archive)
    print(f"✓ Written {NEW_FILE} ({len(new_items)} items)")
    print(f"✓ Written {ARCHIVE_FILE} ({len(archive)} items total)")


if __name__ == "__main__":
    main()
