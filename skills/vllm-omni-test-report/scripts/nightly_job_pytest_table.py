#!/usr/bin/env python3
"""
Fetch vllm-omni Buildkite nightly jobs (excluding Upload * Pipeline, :docker: Build image,
:email: Nightly Collection & Email, :pipeline: init), pull each job raw log,
and emit Markdown rows for a per-job pytest summary table.

Requires: BUILDKITE_TOKEN or BUILDKITE_API_TOKEN in the environment.
Optional: BUILDKITE_BUILD_NUMBER to pin a build; otherwise picks latest main build whose
message matches (?i)scheduled nightly.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from md_table import render_markdown_table

ORG = "vllm"
PIPELINE = "vllm-omni"
BRANCH = "main"

# Ignore artifact/upload steps when reporting test outcomes.
UPLOAD_PIPELINE_RE = re.compile(r"^Upload .+ Pipeline$", re.IGNORECASE)
# Non-test steps: omit from per-job pytest table (no useful pytest footer).
SKIP_NON_PYTEST_JOB_RES = (
    re.compile(r"^:docker:\s*Build image\s*$", re.IGNORECASE),
    re.compile(r"^:email:\s*Nightly Collection\s*&\s*Email\s*$", re.IGNORECASE),
    re.compile(r"^:pipeline:\s*init\s*$", re.IGNORECASE),
)

# Pytest final session lines (6.x/7.x/8.x variants).
SESSION_LINE_RE = re.compile(
    r"^=+\s*.+\s*in\s+[\d.]+s\s*=+\s*$",
)
# e.g. "... 3 failed, 10 passed, 1 skipped ..."
COUNTS_FRAGMENT_RE = re.compile(
    r"(\d+)\s+passed|(\d+)\s+failed|(\d+)\s+skipped|(\d+)\s+error",
    re.IGNORECASE,
)


def http_json(url: str, token: str) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def http_text_tail(
    url: str,
    token: str,
    *,
    max_read: int = 32_000_000,
    tail_keep: int = 10_000_000,
) -> str:
    """Download log; if it exceeds max_read bytes, keep only the last tail_keep bytes."""
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
    )
    buf = bytearray()
    with urllib.request.urlopen(req, timeout=300) as resp:
        while True:
            chunk = resp.read(262_144)
            if not chunk:
                break
            buf.extend(chunk)
            if len(buf) > max_read:
                buf = buf[-tail_keep:]
    return buf.decode("utf-8", errors="replace")


def latest_scheduled_nightly_number(token: str) -> int:
    url = (
        f"https://api.buildkite.com/v2/organizations/{ORG}/pipelines/"
        f"{PIPELINE}/builds?branch={BRANCH}&per_page=50"
    )
    builds = http_json(url, token)
    for b in builds:
        if re.search(r"scheduled\s+nightly", b.get("message") or "", re.I):
            return int(b["number"])
    sys.exit("No scheduled nightly build found on main (per_page=50).")


def should_skip_job(name: str) -> bool:
    n = (name or "").strip()
    if UPLOAD_PIPELINE_RE.match(n):
        return True
    return any(r.match(n) for r in SKIP_NON_PYTEST_JOB_RES)


def parse_pytest(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    failed_nodes: list[str] = []
    error_nodes: list[str] = []
    for line in lines:
        if line.startswith("FAILED "):
            failed_nodes.append(line[7:].strip())
        elif line.startswith("ERROR "):
            error_nodes.append(line[6:].strip())

    summary = None
    for line in reversed(lines):
        s = line.strip()
        if SESSION_LINE_RE.match(s) and COUNTS_FRAGMENT_RE.search(s):
            summary = s.strip().strip("=").strip()
            break
    if summary is None:
        for line in reversed(lines):
            s = line.strip()
            if "short test summary" in s.lower():
                continue
            if COUNTS_FRAGMENT_RE.search(s) and len(s) < 300:
                summary = s
                break

    failed_nodes = list(dict.fromkeys(failed_nodes))
    error_nodes = list(dict.fromkeys(error_nodes))

    return {
        "failed_nodes": failed_nodes,
        "error_nodes": error_nodes,
        "summary": summary,
    }


def job_anchor(build_no: int, job_id: str) -> str:
    return f"https://buildkite.com/{ORG}/{PIPELINE}/builds/{build_no}#{job_id}"


def md_cell(s: str) -> str:
    return (s or "").replace("|", "/")


def emit_markdown(build: dict[str, Any], token: str) -> None:
    build_no = int(build["number"])
    jobs = build.get("jobs") or []

    report_jobs = [j for j in jobs if not should_skip_job(j.get("name") or "")]
    report_jobs.sort(key=lambda x: (x.get("name") or ""))

    rows: list[list[str]] = []

    for j in report_jobs:
        name = md_cell(j.get("name") or "")
        jid = j.get("id") or ""
        state = j.get("state") or ""
        link = job_anchor(build_no, jid)
        raw_url = j.get("raw_log_url") or j.get("log_url")
        if not raw_url:
            rows.append(
                [name, f"{md_cell(state)} — no log URL", f"[open]({link})"]
            )
            continue

        try:
            log = http_text_tail(str(raw_url), token)
        except urllib.error.HTTPError:
            rows.append(
                [name, f"{md_cell(state)} — log fetch failed", f"[open]({link})"]
            )
            continue
        except urllib.error.URLError:
            rows.append(
                [name, f"{md_cell(state)} — log fetch failed", f"[open]({link})"]
            )
            continue
        except TimeoutError:
            rows.append(
                [name, f"{md_cell(state)} — log fetch failed", f"[open]({link})"]
            )
            continue

        info = parse_pytest(log)
        summary = info["summary"]
        fails = info["failed_nodes"]
        errors = info["error_nodes"]

        if summary is None and not fails and not errors:
            rows.append(
                [
                    name,
                    f"{md_cell(state)} — non-pytest or log truncated",
                    f"[open]({link})",
                ]
            )
            continue

        agg_result = md_cell(state or "unknown")
        if fails or errors:
            if fails and errors:
                agg_result = "failed/error"
            elif fails:
                agg_result = "failed"
            else:
                agg_result = "error"
        elif summary and re.search(r"\b[1-9]\d*\s+failed\b", summary, re.I):
            agg_result = "failed"
        elif summary and re.search(r"\b[1-9]\d*\s+error\b", summary, re.I):
            agg_result = "error"
        elif (state == "passed" or state == "finished") and not fails and not errors:
            agg_result = "passed"

        rows.append([name, md_cell(agg_result), f"[open]({link})"])

        for node in fails:
            rows.append([f"{name} — {md_cell(node)}", "failed", f"[open]({link})"])
        for node in errors:
            rows.append([f"{name} — {md_cell(node)}", "error", f"[open]({link})"])

    print("## Per-job test execution (pytest)")
    print()
    print(render_markdown_table(["Job", "Result", "Step link"], rows))


def main() -> None:
    parser = argparse.ArgumentParser(description="Markdown table: nightly jobs vs pytest outcomes.")
    parser.add_argument(
        "--build",
        type=int,
        default=None,
        help="Build number (default: latest scheduled nightly on main).",
    )
    args = parser.parse_args()

    token = (
        os.environ.get("BUILDKITE_API_TOKEN") or os.environ.get("BUILDKITE_TOKEN") or ""
    ).strip()
    if not token:
        print(
            "BUILDKITE_API_TOKEN or BUILDKITE_TOKEN is not set.",
            file=sys.stderr,
        )
        sys.exit(2)

    build_no = args.build if args.build is not None else latest_scheduled_nightly_number(token)
    url = (
        f"https://api.buildkite.com/v2/organizations/{ORG}/pipelines/"
        f"{PIPELINE}/builds/{build_no}"
    )
    build = http_json(url, token)
    emit_markdown(build, token)


if __name__ == "__main__":
    main()
