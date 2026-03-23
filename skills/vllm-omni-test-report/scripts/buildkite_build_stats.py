#!/usr/bin/env python3
"""
Fetch vllm-omni builds from the Buildkite REST API for a date range and compute:

  - Success rate: passed / (passed + failed)
  - Average duration: arithmetic mean wall time (finished_at - created_at) for
    passed/failed builds that have both created_at and finished_at

Three buckets (display names in reports):

  1. ready — non-`main` branches
  2. merge — `main`, ordinary runs (e.g. merged PRs), not the scheduled nightly bucket
  3. nightly — `main`, scheduled / message-heuristic nightly pipeline

Usage:

  Set BUILDKITE_API_TOKEN (or BUILDKITE_TOKEN).
  pip install requests  # if missing
  python scripts/buildkite_build_stats.py [--from YYYY-MM-DD --to YYYY-MM-DD] [--markdown]

If `--from` / `--to` are both omitted, the window is the current UTC calendar month through today (month-start 00:00 UTC to today end UTC). If you pass one, pass both (UTC dates, inclusive).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from dataclasses import dataclass, field

try:
    import requests
except ImportError:
    print("Install requests: pip install requests", file=sys.stderr)
    sys.exit(1)

# API constants
BUILDKITE_API_BASE = "https://api.buildkite.com/v2"
ORG_SLUG = "vllm"
PIPELINE_SLUG = "vllm-omni"

# Only finished builds; passed/failed count toward success rate; canceled/blocked reported separately
FINISHED_STATES = {"passed", "failed", "canceled", "blocked", "skipped", "not_run"}
SUCCESS_STATE = "passed"
FAIL_STATE = "failed"


def default_created_range_utc() -> tuple[str, str]:
    """First day of current UTC month through today (UTC), as YYYY-MM-DD strings."""
    today = datetime.now(timezone.utc).date()
    start = today.replace(day=1)
    return start.isoformat(), today.isoformat()


def parse_buildkite_time(s: str | None) -> datetime | None:
    if not s or not isinstance(s, str):
        return None
    text = s.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def get_api_token() -> str | None:
    token = os.environ.get("BUILDKITE_API_TOKEN") or os.environ.get("BUILDKITE_TOKEN")
    return token.strip() if token else None


def parse_link_header(link: str | None) -> dict[str, str]:
    """Parse RFC 5988 Link header; return rel -> url."""
    if not link:
        return {}
    out = {}
    for part in link.split(","):
        part = part.strip()
        m = re.match(r'<([^>]+)>;\s*rel="([^"]+)"', part)
        if m:
            out[m.group(2).strip().lower()] = m.group(1).strip()
    return out


def fetch_builds(
    token: str,
    created_from: str,
    created_to: str,
    *,
    per_page: int = 100,
) -> list[dict]:
    """Fetch all builds for the pipeline created in [created_from, created_to] (paginated)."""
    url = (
        f"{BUILDKITE_API_BASE}/organizations/{ORG_SLUG}/pipelines/{PIPELINE_SLUG}/builds"
    )
    params = {
        "created_from": created_from,
        "created_to": created_to,
        "per_page": per_page,
    }
    headers = {"Authorization": f"Bearer {token}"}
    all_builds: list[dict] = []

    while True:
        r = requests.get(url, params=params, headers=headers, timeout=60)
        r.raise_for_status()
        data = r.json()
        page = data if isinstance(data, list) else [data]
        all_builds.extend(page)

        link = r.headers.get("Link") or r.headers.get("link")
        links = parse_link_header(link)
        next_url = links.get("next")
        if not next_url:
            break
        # Follow next URL as-is; do not send params again
        url = next_url
        params = {}

    return all_builds


def is_nightly(build: dict) -> bool:
    """True if scheduled or commit message suggests nightly."""
    source = (build.get("source") or "").strip().lower()
    if source == "schedule":
        return True
    msg = (build.get("message") or "").lower()
    if "nightly" in msg or "scheduled" in msg and "build" in msg:
        return True
    return False


def classify_build(build: dict) -> str:
    """Return 'non_main' | 'main_non_nightly' | 'main_nightly'."""
    branch = (build.get("branch") or "").strip()
    main = branch == "main"
    nightly = is_nightly(build)

    if not main:
        return "non_main"
    if nightly:
        return "main_nightly"
    return "main_non_nightly"


@dataclass
class Bucket:
    passed: int = 0
    failed: int = 0
    other_finished: int = 0  # canceled, blocked, etc.
    # Wall-clock seconds for passed/failed builds with both created_at and finished_at
    duration_seconds: list[float] = field(default_factory=list)

    @property
    def total_for_success_rate(self) -> int:
        return self.passed + self.failed

    @property
    def success_rate(self) -> float | None:
        t = self.total_for_success_rate
        if t == 0:
            return None
        return self.passed / t

    @property
    def avg_duration_seconds(self) -> float | None:
        if not self.duration_seconds:
            return None
        return sum(self.duration_seconds) / len(self.duration_seconds)


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    if seconds < 3600:
        m, s = divmod(int(seconds), 60)
        return f"{m}m{s}s"
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h}h{m}m{s}s"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch Buildkite vllm-omni builds; success rate and avg duration by category"
    )
    parser.add_argument(
        "--from",
        dest="created_from",
        default=None,
        metavar="YYYY-MM-DD",
        help=(
            "Start date for Buildkite created_at filter (UTC, inclusive). "
            "Omit both --from and --to to use current UTC month through today."
        ),
    )
    parser.add_argument(
        "--to",
        dest="created_to",
        default=None,
        metavar="YYYY-MM-DD",
        help=(
            "End date for Buildkite created_at filter (UTC, inclusive). "
            "Omit both --from and --to to use current UTC month through today."
        ),
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print each build's category and state",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Also emit a Markdown block for the report (CI details section).",
    )
    args = parser.parse_args()

    if args.created_from is None and args.created_to is None:
        args.created_from, args.created_to = default_created_range_utc()
    elif args.created_from is None or args.created_to is None:
        print(
            "buildkite_build_stats.py: pass both --from and --to, or omit both "
            "(defaults to current UTC month through today).",
            file=sys.stderr,
        )
        return 2

    token = get_api_token()
    if not token:
        print(
            "BUILDKITE_API_TOKEN or BUILDKITE_TOKEN is not set; cannot call the Buildkite API.",
            file=sys.stderr,
        )
        print("Set one in the environment and retry.", file=sys.stderr)
        return 1

    created_from = f"{args.created_from}T00:00:00Z"
    created_to = f"{args.created_to}T23:59:59Z"

    print(f"Fetching {ORG_SLUG}/{PIPELINE_SLUG} builds {args.created_from} ~ {args.created_to}...")
    try:
        builds = fetch_builds(token, created_from, created_to)
    except requests.RequestException as e:
        print(f"API request failed: {e}", file=sys.stderr)
        if hasattr(e, "response") and e.response is not None:
            print(f"HTTP status: {e.response.status_code}", file=sys.stderr)
            print(e.response.text[:500], file=sys.stderr)
        return 1

    print(f"Fetched {len(builds)} build(s).\n")

    buckets: dict[str, Bucket] = defaultdict(Bucket)
    for b in builds:
        state = (b.get("state") or "").strip().lower()
        kind = classify_build(b)
        if args.verbose:
            print(f"  #{b.get('number')} branch={b.get('branch')} state={state} -> {kind}")

        if state not in FINISHED_STATES:
            continue
        bucket = buckets[kind]
        if state == SUCCESS_STATE:
            bucket.passed += 1
        elif state == FAIL_STATE:
            bucket.failed += 1
        else:
            bucket.other_finished += 1

        if state in (SUCCESS_STATE, FAIL_STATE):
            c_at = parse_buildkite_time(b.get("created_at"))
            f_at = parse_buildkite_time(b.get("finished_at"))
            if c_at is not None and f_at is not None:
                delta = (f_at - c_at).total_seconds()
                if delta >= 0:
                    bucket.duration_seconds.append(delta)

    # Print three buckets: success rate and average duration
    labels = {
        "non_main": "ready",
        "main_non_nightly": "merge",
        "main_nightly": "nightly",
    }
    keys_order = ("non_main", "main_non_nightly", "main_nightly")
    print(
        "--- By category (success rate: passed/failed only; avg duration: mean over builds with both timestamps) ---"
    )
    rows_md: list[tuple[str, str, str, str]] = []
    for key in keys_order:
        bucket = buckets[key]
        label = labels[key]
        total = bucket.total_for_success_rate
        if total == 0:
            rate_str = "N/A (no passed/failed builds)"
        else:
            rate = bucket.success_rate
            rate_str = f"{rate * 100:.1f}% ({bucket.passed}/{total})"
        other = bucket.other_finished
        extra = f" (+ {other} other finished: canceled/blocked/etc.)" if other else ""

        avg_sec = bucket.avg_duration_seconds
        if avg_sec is None:
            dur_str = "N/A (no valid created_at/finished_at)"
            dur_md = "N/A"
        else:
            n_timed = len(bucket.duration_seconds)
            dur_str = f"{format_duration(avg_sec)} ({n_timed} build(s) with duration)"
            dur_md = f"{format_duration(avg_sec)} ({n_timed} builds)"

        print(f"  {label}: success rate = {rate_str}{extra}")
        print(f"           avg duration = {dur_str}")
        rows_md.append((label, rate_str.replace("|", "/"), dur_md, str(other)))

    if args.markdown:
        print()
        print("## CI details")
        print()
        print(
            f"Source: `scripts/buildkite_build_stats.py`; "
            f"window (Buildkite `created_at`, UTC): `{args.created_from}` - `{args.created_to}`."
        )
        print()
        print(
            "> Success rate denominator is passed+failed only. Average duration is the mean wall time "
            "(finished_at - created_at) over those passed/failed builds that have both timestamps. "
            "\"Other finished\" counts canceled/blocked/etc.; they are not in the success-rate denominator."
        )
        print()
        print("| CI category | Success rate | Avg duration | Other finished count |")
        print("|-------------|--------------|--------------|----------------------|")
        for label, rate, dur, other in rows_md:
            print(f"| {label} | {rate} | {dur} | {other} |")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
