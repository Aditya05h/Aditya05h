"""Render GitHub's public contribution calendar. Python 3.11+, no packages needed."""
from __future__ import annotations

import argparse
from datetime import date
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
from render_art import render, render_stats


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = []
        self.tooltips = {}
        self.tip_id = None
        self.tip_parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "data-date" in attrs and "data-level" in attrs:
            self.cells.append(attrs)
        if tag == "tool-tip":
            self.tip_id = attrs.get("for")
            self.tip_parts = []

    def handle_data(self, data):
        if self.tip_id is not None:
            self.tip_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self.tip_id is not None:
            self.tooltips[self.tip_id] = "".join(self.tip_parts).strip()
            self.tip_id = None


def validate_days(days):
    if not 300 <= len(days) <= 371:
        raise ValueError(f"Expected a full yearly calendar; received {len(days)} days.")
    dates = [date.fromisoformat(d["date"]) for d in days]
    if dates != sorted(set(dates)):
        raise ValueError("Calendar dates must be unique and sorted.")
    if (dates[-1] - dates[0]).days + 1 != len(dates):
        raise ValueError("Calendar has missing dates.")
    for day in days:
        if not isinstance(day["count"], int) or day["count"] < 0:
            raise ValueError("Invalid contribution count.")
        if day["level"] not in range(5):
            raise ValueError("Unknown contribution level.")
        if (day["count"] == 0) != (day["level"] == 0):
            raise ValueError("Contribution count and color level disagree.")


def parse_calendar(html):
    parser = CalendarParser()
    parser.feed(html)
    days = {}
    for cell in parser.cells:
        text = parser.tooltips.get(cell.get("id"), "")
        match = re.search(r"\b(No|[\d,]+) contributions?\b", text, re.I)
        if not match:
            raise ValueError(f"Cannot read contribution count for {cell['data-date']}.")
        count = 0 if match[1].lower() == "no" else int(match[1].replace(",", ""))
        day = {"date": cell["data-date"], "count": count, "level": int(cell["data-level"])}
        if day["date"] in days and days[day["date"]] != day:
            raise ValueError("Conflicting duplicate dates.")
        days[day["date"]] = day
    result = sorted(days.values(), key=lambda d: d["date"])
    validate_days(result)
    return result


def fetch_calendar(username):
    url = f"https://github.com/users/{username}/contributions"
    request = Request(url, headers={
        "User-Agent": "GitHub-Profile-Calendar/1.0",
        "Accept": "text/html", "Accept-Language": "en-US,en;q=0.9",
    })
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                return parse_calendar(response.read().decode("utf-8"))
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("Calendar request failed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default="Aditya05h")
    parser.add_argument("--render-only", action="store_true", help="Use the saved calendar; no network.")
    parser.add_argument("--from-html", type=Path, help="Read a saved GitHub contribution fragment.")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", args.username):
        parser.error("Invalid GitHub username")
    json_path = ROOT / "data/contributions.json"
    svg_path = ROOT / "assets/contributions.svg"
    if args.render_only:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    else:
        days = parse_calendar(args.from_html.read_text(encoding="utf-8")) if args.from_html else fetch_calendar(args.username)
        data = {"username": args.username, "source": f"https://github.com/users/{args.username}/contributions", "days": days}
    # Parse and render fully before replacing either file. Failures preserve existing art.
    validate_days(data["days"])
    svg = render(data)
    stats = render_stats(data)
    for path, content in [(json_path, json.dumps(data, indent=2) + "\n"), (svg_path, svg + "\n"), (ROOT / "assets/stats.svg", stats + "\n")]:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(path)
    print(f"Rendered {len(data['days'])} days for {data['username']}.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Calendar update failed; existing artwork retained: {exc}", file=sys.stderr)
        sys.exit(1)
