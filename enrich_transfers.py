#!/usr/bin/env python3
"""
One-time enrichment: open each linked article, extract contract length
and birth year, update transfers_all.json and transfers_new.json.
"""
import json, os, re, time
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
YEAR = datetime.now(timezone.utc).year

def fetch_article(url, timeout=10):
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
        return text[:4000]
    except Exception:
        return ""

def haiku_enrich(text):
    if not API_KEY or not text:
        return {}
    prompt = (
        f"Today is {YEAR}. From this basketball article extract:\n"
        "- contract: duration if mentioned (e.g. '1 year', '2+1', '3 years', 'multi-year'), null if not\n"
        f"- birth_year: player birth year as integer, null if not mentioned "
        f"(if article says 'X-year-old', calculate {YEAR} minus X)\n"
        "Return ONLY JSON: {\"contract\": ..., \"birth_year\": ...}\n\n"
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
            return {
                "contract":   r.get("contract") or None,
                "birth_year": int(r["birth_year"]) if r.get("birth_year") else None,
            }
    except Exception as e:
        print(f"    Haiku error: {e}")
    return {}

def main():
    with open("transfers_all.json", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("items", [])
    to_enrich = [t for t in items if t.get("source_url") and not t.get("_visited")
                 and t.get("contract") is None and t.get("birth_year") is None]
    print(f"Total: {len(items)}, To enrich: {len(to_enrich)}")
    enriched = 0
    for i, item in enumerate(to_enrich):
        url = item["source_url"]
        print(f"[{i+1}/{len(to_enrich)}] {item.get('player','?')[:30]} | {url[:55]}")
        text = fetch_article(url)
        if not text:
            print("  fetch failed"); time.sleep(0.5); continue
        result = haiku_enrich(text)
        if result.get("contract") or result.get("birth_year"):
            item["contract"] = result.get("contract")
            item["birth_year"] = result.get("birth_year")
            enriched += 1
            print(f"  contract={result.get('contract')}, birth_year={result.get('birth_year')}")
        else:
            print("  nothing found")
        time.sleep(0.25)
    print(f"\nEnriched {enriched}/{len(to_enrich)} items")
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    with open("transfers_all.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).strftime("%Y-%m-%d")
    new_items = [t for t in items if not t.get("_visited") and t.get("player")
                 and t.get("league") != "News"
                 and not (t.get("pos")=="?" and t.get("from")=="?" and t.get("to")=="?")
                 and (t.get("date") or "9999") >= cutoff]
    new_items.sort(key=lambda x: x.get("date",""), reverse=True)
    with open("transfers_new.json", "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.now(timezone.utc).isoformat(),
                   "count": len(new_items), "items": new_items}, f, ensure_ascii=False)
    print(f"Saved {len(new_items)} to transfers_new.json")

if __name__ == "__main__":
    main()
