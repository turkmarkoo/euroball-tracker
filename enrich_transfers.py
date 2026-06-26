#!/usr/bin/env python3
"""
Enrichment pass: fetch each linked article, extract contract length and
birth year. Calculates years from season references (e.g. 'until 2027/28'
= 2027 - 2026 = 1 year) and from explicit durations.
"""
import json, os, re, time
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
NOW = datetime.now(timezone.utc)
YEAR = NOW.year

def fetch_article(url, timeout=12):
    try:
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        })
        with urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:5000]
    except Exception as e:
        return ""

def haiku_enrich(text, player):
    if not API_KEY or not text:
        return {}
    next2 = YEAR + 2
    next3 = YEAR + 3
    prompt = (
        f"Today is {YEAR}. Current basketball season: {YEAR}-{str(YEAR+1)[-2:]}. "
        f"A season like '{YEAR+1}/{str(YEAR+2)[-2:]}' means the 2nd upcoming season ({YEAR+1}-{str(YEAR+2)[-2:]}), etc.\n"
        f"Player: {player}\n\n"
        "From this basketball article extract:\n"
        "- contract: how long the player signed/extended.\n"
        "  Rules for calculation:\n"
        f"  * Explicit: '2 years', '1+1', 'three-year', 'multi-year' -> use as-is\n"
        f"  * Season end like 'until {YEAR+1}/{str(YEAR+2)[-2:]}' or 'through {YEAR+1}-{str(YEAR+2)[-2:]}': {YEAR+1}-{YEAR}=1 year -> '1 year'\n"
        f"  * Season end like 'until {YEAR+2}/{str(YEAR+3)[-2:]}': {YEAR+2}-{YEAR}=2 years -> '2 years'\n"
        f"  * Season end like 'until {YEAR+3}/{str(YEAR+4)[-2:]}': {YEAR+3}-{YEAR}=3 years -> '3 years'\n"
        f"  * Calendar year 'until {YEAR+1}' or 'till {YEAR+1}': 1 year; 'until {YEAR+2}': 2 years\n"
        "  * If no contract info found: null\n"
        "- birth_year: player birth year as integer, or null\n"
        "  (if article says 'X-year-old', calculate {YEAR} - X)\n"
        "Return ONLY JSON: {\"contract\": \"X year\" or \"X+Y\" or null, \"birth_year\": YYYY or null}\n\n"
        f"Article: {text}"
    )
    body = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 80,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"Content-Type": "application/json", "x-api-key": API_KEY,
                 "anthropic-version": "2023-06-01"},
    )
    try:
        with urlopen(req, timeout=25) as resp:
            data = json.load(resp)
        raw = data["content"][0]["text"].strip()
        m = re.search(r"\{.*?\}", raw, re.DOTALL)
        if m:
            r = json.loads(m.group())
            contract = r.get("contract") or None
            by = r.get("birth_year")
            return {
                "contract":   contract,
                "birth_year": int(by) if by else None,
            }
    except Exception as e:
        print(f"    Haiku error: {e}")
    return {}

def main():
    with open("transfers_all.json", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("items", [])

    # Enrich items missing contract OR birth_year (re-run if only one is missing)
    to_enrich = [t for t in items if t.get("source_url") and not t.get("_visited")
                 and (t.get("contract") is None or t.get("birth_year") is None)]
    print(f"Total: {len(items)}, To enrich: {len(to_enrich)}")

    enriched = 0
    for i, item in enumerate(to_enrich):
        url   = item["source_url"]
        player = item.get("player", "?")
        print(f"[{i+1}/{len(to_enrich)}] {player[:28]} | {url[:55]}")
        text = fetch_article(url)
        if not text:
            print("  fetch failed"); time.sleep(0.5); continue
        result = haiku_enrich(text, player)
        changed = False
        if result.get("contract") and item.get("contract") is None:
            item["contract"] = result["contract"]; changed = True
        if result.get("birth_year") and item.get("birth_year") is None:
            item["birth_year"] = result["birth_year"]; changed = True
        if changed:
            enriched += 1
            print(f"  -> contract={item.get('contract')}, birth_year={item.get('birth_year')}")
        else:
            print("  nothing new")
        time.sleep(0.2)

    print(f"\nEnriched {enriched}/{len(to_enrich)} items")
    data["generated_at"] = NOW.isoformat()
    with open("transfers_all.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    cutoff = (NOW - timedelta(days=14)).strftime("%Y-%m-%d")
    new_items = [t for t in items if not t.get("_visited") and t.get("player")
                 and t.get("league") != "News"
                 and not (t.get("pos")=="?" and t.get("from")=="?" and t.get("to")=="?")
                 and (t.get("date") or "9999") >= cutoff]
    new_items.sort(key=lambda x: x.get("date",""), reverse=True)
    with open("transfers_new.json", "w", encoding="utf-8") as f:
        json.dump({"generated_at": NOW.isoformat(), "count": len(new_items),
                   "items": new_items}, f, ensure_ascii=False)
    print(f"Saved {len(new_items)} to transfers_new.json")

if __name__ == "__main__":
    main()
