#!/usr/bin/env python3
"""
Compose a full Markdown test report:
  - Metrics overview: buildkite_build_stats.py --markdown (first body section)
  - Test content (job scope): embed references/ci-job-test-scope.md
  - Local testing: embed references/local-test-matrix.md
  - CI testing: Buildkite build JSON + nightly_job_pytest_table.py (latest scheduled nightly)
  - CI testing: GitHub Search — label bug + [CI Failure] title prefix (case-insensitive; current UTC month)
  - Open issues: GitHub open bugs (March, UTC, in github_march_bug_rows)

Requires BUILDKITE_TOKEN or BUILDKITE_API_TOKEN in the environment.
Run from skill dir: python scripts/compose_full_report.py
"""

from __future__ import annotations

import argparse
import calendar
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from md_table import render_markdown_table

CI_FAILURE_STANDALONE_RE = re.compile(r"^\[CI Failure\]", re.IGNORECASE)
CI_FAILURE_PREFIX_RE = re.compile(r"^\[Bug\]\s*:\s*\[CI Failure\]", re.IGNORECASE)

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
        r = requests.get(url, headers=h, timeout=timeout, verify=verify)
        r.raise_for_status()
        return r.json()
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


def github_march_bug_rows(
    gh_token: str | None, month_prefix: str
) -> tuple[int, int, str]:
    """Return (open_bug_total, month_count, markdown_table_body). month_prefix = YYYY-MM (UTC)."""
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

    march = [
        i
        for i in all_items
        if str(i.get("created_at") or "").startswith(month_prefix)
    ]
    march.sort(key=lambda x: x["created_at"], reverse=True)
    row_cells: list[list[str]] = []
    for i in march:
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
    return len(all_items), len(march), body


def is_ci_failure_title(title: str) -> bool:
    t = (title or "").strip()
    if CI_FAILURE_STANDALONE_RE.match(t):
        return True
    if CI_FAILURE_PREFIX_RE.match(t):
        return True
    return False


def github_ci_failure_analysis_rows(
    month_prefix: str, gh_token: str | None
) -> tuple[int, str]:
    """Issues labeled bug, title [CI Failure] prefix (case-insensitive), created in month_prefix (YYYY-MM)."""
    y, m = month_prefix.split("-")
    year, mon = int(y), int(m)
    last = calendar.monthrange(year, mon)[1]
    q = (
        f"repo:vllm-project/vllm-omni is:issue label:bug "
        f"created:{month_prefix}-01..{month_prefix}-{last:02d}"
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
            if not is_ci_failure_title(str(i.get("title") or "")):
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


def test_scope_markdown(skill_dir: Path) -> str:
    """Body for ## Test content (job scope) from references/ci-job-test-scope.md (demote ## to ###)."""
    ref = skill_dir / "references" / "ci-job-test-scope.md"
    if not ref.is_file():
        return (
            "## Test content (job scope)\n\n"
            "*(references/ci-job-test-scope.md not found.)*\n"
        )
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
        "## Test content (job scope)\n\n"
        "Canonical source: [references/ci-job-test-scope.md](references/ci-job-test-scope.md).\n\n"
        f"{body}\n"
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
        default="2026-03-01",
        help="buildkite_build_stats.py --from (UTC YYYY-MM-DD)",
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
    today_utc = datetime.now(timezone.utc).date().isoformat()
    stats_to = args.stats_to or today_utc

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

    pytest_md = run_script(
        scripts_dir / "nightly_job_pytest_table.py",
        ["--build", str(build_no)],
        skill_dir,
        env,
    )
    stats_raw = run_script(
        scripts_dir / "buildkite_build_stats.py",
        ["--from", args.stats_from, "--to", stats_to, "--markdown"],
        skill_dir,
        env,
    )
    ci_md = extract_ci_markdown(stats_raw)

    test_scope_md = test_scope_markdown(skill_dir)

    local_md = local_testing_markdown(skill_dir)

    pytest_ci = pytest_md.strip()
    if "## Per-job test execution" in pytest_ci:
        pytest_ci = pytest_ci.replace(
            "## Per-job test execution", "### Per-job test execution", 1
        )

    month_prefix = today_utc[:7]
    gh_token = (
        os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    ).strip() or None
    github_open_error = ""
    try:
        open_total, march_n, issue_rows = github_march_bug_rows(gh_token, month_prefix)
    except Exception as exc:
        open_total = 0
        march_n = 0
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

    try:
        ci_fail_n, ci_fail_rows = github_ci_failure_analysis_rows(month_prefix, gh_token)
        ci_fail_error = ""
    except Exception as exc:
        ci_fail_n = -1
        ci_fail_rows = ""
        ci_fail_error = str(exc)

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

    if ci_fail_error:
        ci_failure_block = (
            f"### Analysis (CI Failure)\n\n"
            f"*GitHub Search API unavailable: {ci_fail_error}.* Fill in manually per "
            f"[references/ci-github-ci-failure-issues.md](references/ci-github-ci-failure-issues.md) "
            f"from [open bugs](https://github.com/vllm-project/vllm-omni/issues/?q=is%3Aissue%20state%3Aopen%20label%3Abug) "
            f"and [closed bugs](https://github.com/vllm-project/vllm-omni/issues/?q=is%3Aissue%20state%3Aclosed%20label%3Abug).\n"
        )
    elif ci_fail_n == 0:
        ci_failure_block = (
            f"### Analysis (CI Failure)\n\n"
            f"**Filter:** `label:bug`, title prefix **`[CI Failure]`** (**case-insensitive**), `created_at` (UTC) in **{month_prefix}**."
            f" **Data sources:** [open `label:bug`](https://github.com/vllm-project/vllm-omni/issues/?q=is%3Aissue%20state%3Aopen%20label%3Abug) · "
            f"[closed `label:bug`](https://github.com/vllm-project/vllm-omni/issues/?q=is%3Aissue%20state%3Aclosed%20label%3Abug).\n\n"
            f"*No matching `label:bug` issues with a case-insensitive `[CI Failure]` title prefix this month ({month_prefix} UTC).*\n"
        )
    else:
        ci_failure_block = (
            f"### Analysis (CI Failure)\n\n"
            f"**Filter:** `label:bug`, title prefix **`[CI Failure]`** (**case-insensitive**), `created_at` (UTC) in **{month_prefix}**."
            f" **Data sources:** [open `label:bug`](https://github.com/vllm-project/vllm-omni/issues/?q=is%3Aissue%20state%3Aopen%20label%3Abug) · "
            f"[closed `label:bug`](https://github.com/vllm-project/vllm-omni/issues/?q=is%3Aissue%20state%3Aclosed%20label%3Abug)."
            f" **Rows in table:** {ci_fail_n}.\n\n"
            f"{ci_fail_rows}\n"
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
## Open issues (current month)

Open issues labeled **bug**, state **open**, **excluding PRs**, with **`created_at`** in **{month_prefix}** (UTC `YYYY-MM` prefix): **{march_n}** (total open `bug` issues when fetched: **{open_total}**).{github_open_note}

{issue_rows}

## Data source

- Job scope: `references/ci-job-test-scope.md`
- Local matrix: `references/local-test-matrix.md`
- Buildkite API: `{ORG}/{PIPELINE}` branch `main`
- `scripts/nightly_job_pytest_table.py --build {build_no}`
- `scripts/buildkite_build_stats.py --from {args.stats_from} --to {stats_to} --markdown` (includes GitHub bug first-response for metrics table)
- GitHub: `GET /repos/vllm-project/vllm-omni/issues?state=open&labels=bug` (paginated, open issues section)
- GitHub Search: `[CI Failure]`-prefixed bug issues (current month, case-insensitive prefix); see `references/ci-github-ci-failure-issues.md`
"""
    out_path.write_text(md, encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
