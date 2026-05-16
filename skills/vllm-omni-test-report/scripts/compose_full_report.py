#!/usr/bin/env python3
"""
Compose a full Markdown test report:
  - Metrics overview: buildkite_build_stats.py --markdown (first body section)
  - Test content (job scope): rows from the resolved scheduled nightly (reportable jobs) +
    Scope / intent looked up from references/ci-job-test-scope.md
  - Local testing: embed references/local-test-matrix.md
  - CI testing: Buildkite build JSON + nightly_job_pytest_table.py (latest scheduled nightly)
  - CI testing: GitHub Search — label:bug + label:ci-failure; created range matches --stats-from/--stats-to
  - Open issues: GitHub open bugs (label:bug); filter `created_at` to --stats-from..--stats-to (UTC)

Requires BUILDKITE_TOKEN or BUILDKITE_API_TOKEN in the environment.
Run from skill dir: python scripts/compose_full_report.py
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from md_table import render_markdown_table

CI_FAILURE_LABEL = "ci-failure"  # matches GitHub label on vllm-project/vllm-omni

ORG = "vllm"
PIPELINE = "vllm-omni"
BRANCH = "main"
UPLOAD_PIPELINE_RE = re.compile(r"^Upload .+ Pipeline$", re.IGNORECASE)


def _github_tls_verify() -> bool:
    """Same as ``GITHUB_INSECURE_SSL`` in ``buildkite_build_stats.py`` (GitHub API only)."""
    v = (os.environ.get("GITHUB_INSECURE_SSL") or "").strip().lower()
    if v in ("1", "true", "yes", "on"):
        return False
    return True


if not _github_tls_verify():
    try:
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except Exception:
        pass


def http_get_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 120,
) -> object:
    """
    GET JSON from ``url``. Prefer ``requests`` when installed (better TLS/proxy behavior on some
    Windows setups); fall back to :mod:`urllib`.

    For ``api.github.com``, TLS verification follows ``GITHUB_INSECURE_SSL`` (see
    ``buildkite_build_stats.py``). Other hosts always verify.
    """
    h = dict(headers or {})
    verify = True
    if "api.github.com" in url:
        verify = _github_tls_verify()
    try:
        import requests
    except ImportError:
        requests = None
    if requests is not None:
        last_err: Exception | None = None
        for attempt in range(12):
            try:
                r = requests.get(url, headers=h, timeout=timeout, verify=verify)
                if r.status_code == 429:
                    ra = r.headers.get("Retry-After", "60")
                    try:
                        wait_s = int(float(ra)) + 1
                    except ValueError:
                        wait_s = 61
                    time.sleep(min(180, max(1, wait_s)))
                    continue
                r.raise_for_status()
                return r.json()
            except requests.RequestException as e:
                last_err = e
                if attempt < 11:
                    time.sleep(min(8, 2 ** min(attempt, 3)))
        assert last_err is not None
        raise last_err
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def http_json(url: str, token: str | None = None) -> object:
    headers: dict[str, str] = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return http_get_json(url, headers=headers, timeout=120)


def latest_scheduled_nightly_number(token: str) -> int:
    url = (
        f"https://api.buildkite.com/v2/organizations/{ORG}/pipelines/"
        f"{PIPELINE}/builds?branch={BRANCH}&per_page=50"
    )
    builds = http_json(url, token)
    assert isinstance(builds, list)
    for b in builds:
        if re.search(r"scheduled\s+nightly", (b.get("message") or ""), re.I):
            return int(b["number"])
    sys.exit("No scheduled nightly build found on main (per_page=50).")


def _issue_created_date_utc(issue: dict) -> str | None:
    """``YYYY-MM-DD`` from GitHub ``created_at`` or ``None``."""
    ca = issue.get("created_at")
    if not ca or not isinstance(ca, str):
        return None
    s = ca.strip().replace("Z", "+00:00")
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return None


def github_open_bug_rows_in_range(
    gh_token: str | None,
    date_from: str,
    date_to: str,
) -> tuple[int, int, str]:
    """
    Paginate **open** issues with label ``bug`` (PR entries excluded).

    Return ``(total_open_bug_fetched, count_in_created_range, markdown_table)``.
    ``count_in_created_range`` = issues whose **UTC calendar date** of ``created_at``
    lies in ``[date_from, date_to]`` inclusive (``YYYY-MM-DD`` strings).
    """
    base = "https://api.github.com/repos/vllm-project/vllm-omni/issues"
    all_items: list = []
    page = 1
    headers: dict[str, str] = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "vllm-omni-compose-report",
    }
    if gh_token:
        headers["Authorization"] = f"Bearer {gh_token}"
    while True:
        url = f"{base}?state=open&labels=bug&per_page=100&page={page}"
        batch = http_get_json(url, headers=headers, timeout=60)
        if not batch:
            break
        for i in batch:
            if i.get("pull_request"):
                continue
            all_items.append(i)
        if len(batch) < 100:
            break
        page += 1

    in_range = [
        i
        for i in all_items
        if (d := _issue_created_date_utc(i)) is not None and date_from <= d <= date_to
    ]
    in_range.sort(key=lambda x: x["created_at"], reverse=True)
    row_cells: list[list[str]] = []
    for i in in_range:
        t = (i.get("title") or "").replace("|", "\\|").replace("\n", " ")
        u = (i.get("user") or {}).get("login", "")
        row_cells.append(
            [
                f"[#{i['number']}](https://github.com/vllm-project/vllm-omni/issues/{i['number']})",
                t,
                str(i["created_at"])[:10],
                "open",
                f"@{u}",
            ]
        )
    body = render_markdown_table(
        ["Issue", "Title", "Opened at", "Status", "Owner"],
        row_cells,
    )
    return len(all_items), len(in_range), body


def render_open_issues_section(
    stats_from: str,
    stats_to: str,
    gh_token: str | None,
) -> str:
    """Markdown for ``## Open issues`` block (GitHub REST, open ``label:bug`` only)."""
    github_open_error = ""
    try:
        open_total, open_range_n, issue_rows = github_open_bug_rows_in_range(
            gh_token, stats_from, stats_to
        )
    except Exception as exc:
        open_total = 0
        open_range_n = 0
        issue_rows = render_markdown_table(
            ["Issue", "Title", "Opened at", "Status", "Owner"],
            [
                [
                    "*—*",
                    "*Failed to fetch; set `GITHUB_TOKEN` or fill in manually*",
                    "*—*",
                    "*—*",
                    "*—*",
                ]
            ],
        )
        github_open_error = str(exc)

    github_open_note = (
        f" **Note:** open-bugs fetch failed (`{github_open_error}`)."
        if github_open_error
        else ""
    )
    return (
        f"## Open issues (stats window)\n\n"
        f"Open issues labeled **bug**, state **open**, **excluding PRs**, with **`created_at`** "
        f"(UTC date) in **{stats_from}** … **{stats_to}** (same as Buildkite **`--stats-from`** / "
        f"**`--stats-to`**): **{open_range_n}** (total open `bug` issues when fetched: "
        f"**{open_total}**).{github_open_note}\n\n"
        f"{issue_rows}\n"
    )


def github_ci_failure_analysis_rows(
    created_from: str,
    created_to: str,
    gh_token: str | None,
) -> tuple[int, str]:
    """
    Issues with labels ``bug`` and ``ci-failure``, ``created_at`` (UTC) in
    ``created_from`` .. ``created_to`` (inclusive, YYYY-MM-DD).

    Same date window as ``compose_full_report.py`` ``--stats-from`` / ``--stats-to``
    (Buildkite metrics window).
    """
    q = (
        f"repo:vllm-project/vllm-omni is:issue label:bug label:{CI_FAILURE_LABEL} "
        f"created:{created_from}..{created_to}"
    )
    base = "https://api.github.com/search/issues?q=" + urllib.parse.quote(q)
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "vllm-omni-compose-report",
    }
    if gh_token:
        headers["Authorization"] = f"Bearer {gh_token}"

    collected: list[dict] = []
    page = 1
    while True:
        url = f"{base}&per_page=100&page={page}"
        data = http_get_json(url, headers=headers, timeout=120)
        items = data.get("items") or []
        if not items:
            break
        for i in items:
            if i.get("pull_request"):
                continue
            collected.append(i)
        if len(items) < 100:
            break
        page += 1

    collected.sort(key=lambda x: int(x.get("number", 0)), reverse=True)
    row_cells: list[list[str]] = []
    for i in collected:
        num = i["number"]
        title = (i.get("title") or "").replace("|", "\\|").replace("\n", " ")
        st = (i.get("state") or "").lower()
        status_label = "Closed" if st == "closed" else "Open"
        link = f"https://github.com/vllm-project/vllm-omni/issues/{num}"
        row_cells.append([f"[#{num}]({link})", title, status_label])
    if not row_cells:
        return 0, ""
    return len(collected), render_markdown_table(
        ["Issue #", "Title", "Status"], row_cells
    )


def render_ci_failure_section(
    stats_from: str,
    stats_to: str,
    gh_token: str | None,
) -> str:
    """
    Markdown for ``### Analysis (CI Failure)`` … (GitHub Search only; no Buildkite).

    Used by ``compose_full_report.py`` and ``patch_report_ci_failure.py``.
    """
    try:
        ci_fail_n, ci_fail_rows = github_ci_failure_analysis_rows(
            stats_from, stats_to, gh_token
        )
        ci_fail_error = ""
    except Exception as exc:
        ci_fail_n = -1
        ci_fail_rows = ""
        ci_fail_error = str(exc)

    ci_filter_note = (
        f"**Filter:** `label:bug` **and** `label:{CI_FAILURE_LABEL}`, "
        f"`created` (UTC) **{stats_from}** … **{stats_to}** (same window as Buildkite metrics / "
        f"`--stats-from` / `--stats-to`). "
        f"**Cross-check:** "
        f"[issues · bug + ci-failure](https://github.com/vllm-project/vllm-omni/issues?q=is%3Aissue+label%3Abug+label%3Aci-failure)."
    )
    if ci_fail_error:
        return (
            f"### Analysis (CI Failure)\n\n"
            f"*GitHub Search API unavailable: {ci_fail_error}.* Fill in manually per "
            f"[references/ci-github-ci-failure-issues.md](references/ci-github-ci-failure-issues.md) "
            f"from [open bugs](https://github.com/vllm-project/vllm-omni/issues/?q=is%3Aissue%20state%3Aopen%20label%3Abug) "
            f"and [closed bugs](https://github.com/vllm-project/vllm-omni/issues/?q=is%3Aissue%20state%3Aclosed%20label%3Abug).\n"
        )
    if ci_fail_n == 0:
        return (
            f"### Analysis (CI Failure)\n\n"
            f"{ci_filter_note}\n\n"
            f"*No matching issues in this date range.*\n"
        )
    return (
        f"### Analysis (CI Failure)\n\n"
        f"{ci_filter_note}"
        f" **Rows in table:** {ci_fail_n}.\n\n"
        f"{ci_fail_rows}\n"
    )


def run_script(py: Path, args: list[str], cwd: Path, env: dict[str, str]) -> str:
    cmd = [sys.executable, str(py)] + args
    child_env = dict(env)
    child_env.setdefault("PYTHONIOENCODING", "utf-8")
    if sys.platform == "win32":
        child_env.setdefault("PYTHONUTF8", "1")
    p = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=child_env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=3600,
    )
    if p.returncode != 0:
        sys.stderr.write(p.stderr or "")
        sys.exit(f"Command failed ({p.returncode}): {' '.join(cmd)}")
    return p.stdout or ""


def extract_ci_markdown(stats_stdout: str) -> str:
    heading = "## Metrics overview"
    if heading not in stats_stdout:
        return stats_stdout.strip()
    part = stats_stdout.split(heading, 1)[1]
    if "Done." in part:
        part = part.split("Done.", 1)[0]
    return (heading + part).strip()


def _job_scope_ref_lookup_key(cell: str) -> str:
    """First column of a scope table row -> lookup key (matches Buildkite `job.name`)."""
    t = (cell or "").replace("**", "").strip()
    if " (" in t:
        t = t.split(" (", 1)[0].strip()
    return t


def load_job_scope_lookup(ref_path: Path) -> dict[str, str]:
    """
    Parse pipe tables in ``ci-job-test-scope.md`` -> job name -> scope / intent (second column).

    Skips separator rows and header cells ``Typical job name`` / ``Source``.
    """
    if not ref_path.is_file():
        return {}
    lookup: dict[str, str] = {}
    for line in ref_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        parts = [p.strip() for p in s.split("|")[1:-1]]
        if len(parts) < 2:
            continue
        k_raw, scope = parts[0], parts[1]
        if not k_raw or re.match(r"^:?-+:?$", k_raw):
            continue
        key = _job_scope_ref_lookup_key(k_raw)
        low = key.lower()
        if low in ("typical job name", "source"):
            continue
        if not key:
            continue
        lookup[key] = scope.replace("|", "/")
    return lookup


def render_job_scope_section(build: dict, build_no: int, skill_dir: Path) -> str:
    """
    ``## Test content (job scope)``: one row per **reportable** job in this nightly
    (same rule as Summary: omit ``Upload * Pipeline``), scope text from reference lookup.
    """
    ref = skill_dir / "references" / "ci-job-test-scope.md"
    lookup = load_job_scope_lookup(ref)
    jobs = build.get("jobs") or []
    reportable = [
        j
        for j in jobs
        if not UPLOAD_PIPELINE_RE.match((j.get("name") or "").strip())
    ]
    reportable.sort(key=lambda x: (x.get("name") or ""))
    missing = "*—* *(not in reference; add to [references/ci-job-test-scope.md](references/ci-job-test-scope.md) or see log)*"
    rows: list[list[str]] = []
    for j in reportable:
        name = (j.get("name") or "").replace("|", "/")
        st = (j.get("state") or "").replace("|", "/")
        jid = j.get("id") or ""
        link = f"[open](https://buildkite.com/{ORG}/{PIPELINE}/builds/{build_no}#{jid})"
        scope = lookup.get(name.strip(), missing)
        rows.append([name, st, link, scope])
    table = render_markdown_table(
        ["Job (this nightly)", "State", "Step link", "Scope / intent"],
        rows,
    )
    return (
        "## Test content (job scope)\n\n"
        f"Jobs match **scheduled nightly** "
        f"[#{build_no}](https://buildkite.com/{ORG}/{PIPELINE}/builds/{build_no}) "
        "(**reportable** only: `Upload * Pipeline` omitted). "
        "**Scope / intent** is looked up from "
        "[references/ci-job-test-scope.md](references/ci-job-test-scope.md) "
        "by exact job name (see categorized reference for maintenance).\n\n"
        f"{table}\n"
    )


def local_testing_markdown(skill_dir: Path) -> str:
    """Body for ## Local testing from references/local-test-matrix.md (demote ## to ###)."""
    ref = skill_dir / "references" / "local-test-matrix.md"
    if not ref.is_file():
        return "## Local testing\n\n*(references/local-test-matrix.md not found.)*\n"
    raw = ref.read_text(encoding="utf-8")
    lines = raw.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    while lines and not lines[0].strip():
        lines.pop(0)
    out: list[str] = []
    for line in lines:
        if line.startswith("## ") and not line.startswith("### "):
            line = "### " + line[3:]
        out.append(line)
    body = "\n".join(out).strip()
    return (
        "## Local testing\n\n"
        "Canonical source: [references/local-test-matrix.md](references/local-test-matrix.md).\n\n"
        f"{body}\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Compose full vllm-omni test report Markdown.")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output Markdown path (default: <skill-dir>/vllm-omni-test-report-YYYY-MM-DD.md)",
    )
    parser.add_argument(
        "--stats-from",
        default=None,
        help=(
            "buildkite_build_stats.py --from (UTC YYYY-MM-DD). "
            "Default: first day of current UTC month (month-to-date, matches SKILL)."
        ),
    )
    parser.add_argument(
        "--stats-to",
        default=None,
        help="buildkite_build_stats.py --to (default: today UTC)",
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

    skill_dir = Path(__file__).resolve().parent.parent
    scripts_dir = skill_dir / "scripts"
    today_d = datetime.now(timezone.utc).date()
    today_utc = today_d.isoformat()
    stats_to = args.stats_to or today_utc
    stats_from = args.stats_from or today_d.replace(day=1).isoformat()

    build_no = latest_scheduled_nightly_number(token)
    build_url = (
        f"https://api.buildkite.com/v2/organizations/{ORG}/pipelines/"
        f"{PIPELINE}/builds/{build_no}"
    )
    build = http_json(build_url, token)
    assert isinstance(build, dict)

    jobs = build.get("jobs") or []
    reportable = [j for j in jobs if not UPLOAD_PIPELINE_RE.match((j.get("name") or "").strip())]
    states = [(j.get("state") or "").lower() for j in reportable]
    passed = sum(1 for s in states if s == "passed")
    failed = sum(1 for s in states if s in ("failed", "broken"))
    skipped = sum(1 for s in states if s in ("skipped", "not_run", "blocked"))

    commit = build.get("commit") or ""
    short = commit[:7] if len(commit) >= 7 else commit
    env = os.environ.copy()

    stats_raw = run_script(
        scripts_dir / "buildkite_build_stats.py",
        ["--from", stats_from, "--to", stats_to, "--markdown"],
        skill_dir,
        env,
    )
    ci_md = extract_ci_markdown(stats_raw)

    pytest_md = run_script(
        scripts_dir / "nightly_job_pytest_table.py",
        ["--build", str(build_no)],
        skill_dir,
        env,
    )

    test_scope_md = render_job_scope_section(build, build_no, skill_dir)

    local_md = local_testing_markdown(skill_dir)

    pytest_ci = pytest_md.strip()
    if "## Per-job test execution" in pytest_ci:
        pytest_ci = pytest_ci.replace(
            "## Per-job test execution", "### Per-job test execution", 1
        )

    gh_token = (
        os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    ).strip() or None
    open_issues_block = render_open_issues_section(stats_from, stats_to, gh_token)

    ci_failure_block = render_ci_failure_section(stats_from, stats_to, gh_token)

    out_path = args.out
    if out_path is None:
        out_path = skill_dir / f"vllm-omni-test-report-{today_utc}.md"

    failed_jobs_rows: list[list[str]] = []
    for j in reportable:
        st = (j.get("state") or "").lower()
        if st in ("failed", "broken"):
            name = (j.get("name") or "").replace("|", "/")
            jid = j.get("id") or ""
            link = f"https://buildkite.com/{ORG}/{PIPELINE}/builds/{build_no}#{jid}"
            failed_jobs_rows.append([name, st, "See step log", f"[open]({link})"])

    failed_section = (
        render_markdown_table(
            ["Step / Job", "State", "Notes", "Step link"],
            failed_jobs_rows,
        )
        if failed_jobs_rows
        else "*None.*"
    )

    build_table_md = render_markdown_table(
        ["Field", "Value"],
        [
            [
                "**Build**",
                f"[{build_no}](https://buildkite.com/{ORG}/{PIPELINE}/builds/{build_no})",
            ],
            ["**Branch**", build.get("branch") or "main"],
            [
                "**Commit**",
                f"`{short}` ([full](https://github.com/vllm-project/vllm-omni/commit/{commit}))",
            ],
            ["**Trigger**", "Scheduled nightly"],
            ["**Started**", str(build.get("created_at") or "*unknown*")],
            ["**Finished**", str(build.get("finished_at") or "*unknown*")],
            ["**Pipeline state**", str(build.get("state") or "*unknown*")],
            [
                "**Note**",
                "`Upload * Pipeline` steps omitted from test summaries below",
            ],
        ],
    )

    md = f"""# vLLM-Omni Test Report - Scheduled Nightly

{ci_md}

{test_scope_md}

{local_md}
## CI testing (Buildkite — Scheduled nightly)

### Build

{build_table_md}

### Summary (reportable jobs only)

- **Passed**: {passed} jobs
- **Failed / broken**: {failed} jobs
- **Skipped / blocked / not_run**: {skipped} (if any)

### Failed test jobs (if any)

{failed_section}

{pytest_ci}

{ci_failure_block}
{open_issues_block}
## Data source

- Job scope: build **#{build_no}** reportable jobs × `references/ci-job-test-scope.md` (Scope / intent lookup)
- Local matrix: `references/local-test-matrix.md`
- Buildkite API: `{ORG}/{PIPELINE}` branch `main`
- `scripts/nightly_job_pytest_table.py --build {build_no}`
- `scripts/buildkite_build_stats.py --from {stats_from} --to {stats_to} --markdown` (**bugs (first response, …)** = GitHub `label:bug` issues with `created_at` UTC date in the same `--from`..`--to` window)
- GitHub: `GET /repos/vllm-project/vllm-omni/issues?state=open&labels=bug` (paginated); **Open issues** table = issues with `created_at` **UTC date** in `--stats-from`..`--stats-to`
- GitHub Search: `label:bug` + `label:ci-failure`, `created` = `--stats-from`..`--stats-to` (UTC); see `references/ci-github-ci-failure-issues.md`
"""
    out_path.write_text(md, encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
