---
name: vllm-omni-test-report
description: Writes a Markdown test report: first **Metrics overview** (CI stats + GitHub bug first-response + UT coverage from scripts/buildkite_build_stats.py), then **Test content (job scope)** (references/ci-job-test-scope.md), **Local testing** (references/local-test-matrix.md: test results analysis / issue tracking / matrix), and **CI testing** (Buildkite Scheduled nightly: jobs, pytest tables from logs; **Analysis (CI Failure)** table from GitHub `label:bug` + `[CI Failure]` title prefix (case-insensitive) per references/ci-github-ci-failure-issues.md; excludes Upload * Pipeline from test summaries), then paginated open bug issues. Use when generating CI/nightly summaries, Buildkite reports for vllm-omni, analyzing Scheduled nightly results from https://buildkite.com/vllm/vllm-omni/builds?branch=main, or documenting local vs CI CUDA/hardware/software coverage in one report.
---

# vLLM-Omni Test Report (Buildkite Nightly)

## Overview

Generate a **human-readable test report** whose body (excluding **Open issues** at the end) is ordered as:

1. **Metrics overview** — Table with **Success rate/UT coverage**, **Bug avg first response** (GitHub open+closed `label=bug`, current UTC month), plus **ut** / **ut (exclude models)** from **Simple Unit Test** on the **latest non-nightly `main` build** (see [main builds](https://buildkite.com/vllm/vllm-omni/builds?branch=main); same nightly heuristic as merge bucket in `buildkite_build_stats.py`), from [scripts/buildkite_build_stats.py](scripts/buildkite_build_stats.py) (`--markdown`; optional `GITHUB_TOKEN`). This is the **first** top-level section after the title.
2. **Test content (job scope)** — What each common **Buildkite job** is meant to test (Scheduled nightly-oriented), from [references/ci-job-test-scope.md](references/ci-job-test-scope.md). Update when pipeline job names or scopes change.
3. **Local testing** — **Test results analysis** and **Issue tracking** from [references/local-test-matrix.md](references/local-test-matrix.md) (CUDA/hardware/deps/testers + per-row case counts + issue table). No Buildkite API; update that file when local QA scope or a test round’s results change.
4. **CI testing** — Resolve a **Scheduled nightly** build on [vllm-omni `main`](https://buildkite.com/vllm/vllm-omni/builds?branch=main), fetch **reportable** jobs, summarize pass/fail, add **per-job pytest** tables from step logs (exclude `Upload * Pipeline` from test-focused summaries), and add **### Analysis (CI Failure)** (GitHub `label:bug`, title prefix `[CI Failure]` **ignore case**, current UTC month — see [references/ci-github-ci-failure-issues.md](references/ci-github-ci-failure-issues.md); cross-check [open](https://github.com/vllm-project/vllm-omni/issues/?q=is%3Aissue%20state%3Aopen%20label%3Abug) / [closed](https://github.com/vllm-project/vllm-omni/issues/?q=is%3Aissue%20state%3Aclosed%20label%3Abug) bug lists).

Then append **Open issues** (paginated GitHub bugs) unchanged.

## When to Apply

- User asks for a nightly / CI test report for vllm-omni
- User pastes a Buildkite build URL or build number
- User wants to summarize failures, flaky steps, or duration from Buildkite
- User needs **local** matrix content in the report (from [references/local-test-matrix.md](references/local-test-matrix.md)) alongside **CI** results from Buildkite

## Definitions

| Term | Meaning |
|------|---------|
| **Scheduled nightly build** | A build whose **message/title** contains `Scheduled nightly build` (Buildkite scheduled job). It is **not** the same as arbitrary `main` commits. |
| **Latest** | Among matching builds, the one with the **most recent** `finished_at` or `created_at` (prefer finished if both present). |
| **Reportable job** | Any `jobs[]` entry whose **name** does **not** match `(?i)^Upload .+ Pipeline$` (exclude `Upload Ready/Nightly/Merge Pipeline` and similar upload-only steps). |

## Buildkite authentication (environment only)

- All Buildkite REST calls and skill scripts read **`BUILDKITE_TOKEN`** or **`BUILDKITE_API_TOKEN`** from the **process environment** (either name works for the scripts; use one consistently in CI).
- **Do not** paste the secret into chat, pass it on the command line, or embed it in files committed to git. If unset, ask the user to **export it in their local shell** or **configure it as a CI/secret env var**, then retry.
- Before `curl` or Python helpers, confirm the variable is set in the same shell (e.g. bash: `[ -n "${BUILDKITE_TOKEN:-}" ] || [ -n "${BUILDKITE_API_TOKEN:-}" ]`; PowerShell: `if (-not $env:BUILDKITE_TOKEN -and -not $env:BUILDKITE_API_TOKEN) { ... }`).

## Workflow

**Local testing:** There is no API step. When writing the report, **read** [references/local-test-matrix.md](references/local-test-matrix.md) and paste *Common stack*, *Test results analysis*, and *Issue tracking* into **## Local testing** (or use a user-supplied replacement; prefer the user’s values if they paste an updated matrix).

**CI testing, Metrics overview, open issues:** Follow the steps below.

### Step 1: Resolve the target build (CI testing)

**Option A - API (recommended)**

1. Ensure **`BUILDKITE_TOKEN` or `BUILDKITE_API_TOKEN`** is set in the environment for the session that runs `curl` / scripts.
2. If missing, **do not** ask for the raw token in chat. Prompt the user to set it locally (or in CI), e.g. *"Set read-only Buildkite API token in the environment as `BUILDKITE_TOKEN` or `BUILDKITE_API_TOKEN`, then ask again."* Offer **Option C** (web-only fallback) if they cannot use env-based auth.
3. With the env var set, list builds on `main`:

```bash
curl -s -H "Authorization: Bearer $BUILDKITE_TOKEN" \
  "https://api.buildkite.com/v2/organizations/vllm/pipelines/vllm-omni/builds?branch=main&per_page=30" \
  | jq '.'
```

4. Select the **first** build in the array where `.message` matches `(?i)scheduled nightly` **or** the build is clearly labeled as scheduled in the UI message.
5. If none match, report that no scheduled nightly was found in the page and optionally fall back to the **most recent green/red `main` build** only if the user agrees.

**Option B - User-provided build**

If the user gives a URL like `https://buildkite.com/vllm/vllm-omni/builds/<number>`:

```bash
curl -s -H "Authorization: Bearer $BUILDKITE_TOKEN" \
  "https://api.buildkite.com/v2/organizations/vllm/pipelines/vllm-omni/builds/<number>" | jq '.'
```

**Option C - No env token / user prefers web-only**

- Clearly state that without **`BUILDKITE_TOKEN` / `BUILDKITE_API_TOKEN`** in the environment you can only produce a **summary-level** report (build status/duration), not full step/job breakdown.
- Open the [builds list](https://buildkite.com/vllm/vllm-omni/builds?branch=main) and locate the topmost **Scheduled nightly build** entry.
- Ask the user to paste the **build number** or **full build URL** (and optional failing log snippets) for fallback reporting.

### Step 2: Fetch jobs and steps (exclude Upload pipelines)

For the chosen `build_number`:

```bash
curl -s -H "Authorization: Bearer $BUILDKITE_TOKEN" \
  "https://api.buildkite.com/v2/organizations/vllm/pipelines/vllm-omni/builds/<build_number>" \
  | jq '{
      state, message, commit, branch, created_at, finished_at,
      reportable_jobs: [.jobs[] | select(.name | test("^Upload .+ Pipeline$"; "i") | not)
        | {name, state, id, raw_log_url, log_url}]
    }'
```

- **Summary counts** (passed / failed / skipped / broken): count **only** `reportable_jobs`, not upload steps.
- **Failed steps** tables: include only reportable jobs (upload failures must **not** pollute "test failure" narrative unless the user explicitly asks for pipeline hygiene).

### Step 2b: Per-job pytest results (detailed table)

1. For **each reportable job**, GET `raw_log_url` (fallback `log_url`) with `Authorization: Bearer` using the same credential as in [Buildkite authentication (environment only)](#buildkite-authentication-environment-only).
2. Parse pytest output from the log (session `=== ... ===` footer; `FAILED` / `ERROR` lines). See [references/buildkite-api.md](references/buildkite-api.md).
3. **Helper (recommended):** run from the skill directory (requires `BUILDKITE_TOKEN` or `BUILDKITE_API_TOKEN` already exported in that shell):

```bash
python scripts/nightly_job_pytest_table.py              # latest scheduled nightly
python scripts/nightly_job_pytest_table.py --build 4708
```

Paste the emitted **Per-job test execution (pytest)** Markdown table into the **CI testing** section (**### Per-job test execution (pytest)**). The script already **skips** `Upload * Pipeline` jobs.

### Step 2c: Metrics overview (success rate and average duration)

1. From the skill directory, run [scripts/buildkite_build_stats.py](scripts/buildkite_build_stats.py) with `BUILDKITE_TOKEN` or `BUILDKITE_API_TOKEN` set. Optional `GITHUB_TOKEN` (or `GH_TOKEN`) for the **Bug avg first response** column. The script uses `requests` (`pip install requests` if needed).
2. Optional: pass `--from` / `--to` as `YYYY-MM-DD` (UTC, inclusive) for a custom window. If **both are omitted**, the script uses **the current UTC calendar month through today** (month-to-date). To override one past month, pass both dates (e.g. `--from 2025-01-01 --to 2025-01-31`).
3. Add `--markdown` to print a ready-to-paste **Metrics overview** block: Source line plus CI category table (**Success rate/UT coverage**; **Bug avg first response** on **bugs (first response, YYYY-MM)** row from GitHub; **ut** / **ut (exclude models)** from **Simple Unit Test** log parsing — implementation detail stays in `buildkite_build_stats.py`, not in the pasted report prose).

```bash
pip install requests   # if not already installed
python scripts/buildkite_build_stats.py --markdown
# Or an explicit UTC window (must pass both --from and --to together):
# python scripts/buildkite_build_stats.py --from YYYY-MM-DD --to YYYY-MM-DD --markdown
```

4. Paste the full script output (the `## Metrics overview` section through the main metrics table, including **ut**, **ut (exclude models)**, and **bugs (first response, ...)** rows) into the report as the **first** body section (immediately after the report title). **Do not** hand-edit numbers or coverage; they must match the script run.

See [references/buildkite-api.md](references/buildkite-api.md) for how builds are classified into **ready** / **merge** / **nightly** buckets.

### Step 2d: CI testing — `[CI Failure]` GitHub issues (current month)

1. Enumerate issues with **`label:bug`**, title prefix **`[CI Failure]`** (case-insensitive; see [references/ci-github-ci-failure-issues.md](references/ci-github-ci-failure-issues.md)), and **`created_at`** in the **current UTC calendar month** (same `YYYY-MM` window as **Open issues** unless the report specifies another month).
2. Prefer **GitHub Search API**: `GET /search/issues?q=repo:vllm-project/vllm-omni+is:issue+label:bug+created:YYYY-MM-01..YYYY-MM-DD` then **filter** each hit’s `title` with the prefix rules (do **not** treat “CI failure” in free text as a match). Include **open** and **closed** issues that satisfy the filter.
3. Optional: `GITHUB_TOKEN` / `GH_TOKEN` in the environment for higher rate limits (do not paste tokens into chat).
4. Add **### Analysis (CI Failure)** under **CI testing** with columns **Issue #** | **Title** | **Status** (`Open` / `Closed`). If none match, state that explicitly.
5. **compose_full_report.py** fills this subsection automatically when the Search API succeeds.

### Step 3: Fetch **all** open bug issues (paginated)

Do **not** rely on the GitHub web UI first page for counts or tables - it is incomplete when there are many issues.

1. Prefer **GitHub REST API** pagination: `GET /repos/vllm-project/vllm-omni/issues?state=open&labels=bug&per_page=100&page=...` until a page has **fewer than 100** items (or empty). Merge pages; **exclude** entries with `pull_request` (PRs masquerading as issues).
2. If `GITHUB_TOKEN` is missing and you hit rate limits or need stable automation, **prompt the user** (e.g. `Provide GITHUB_TOKEN to paginate all open bugs reliably and avoid unauthenticated rate limits.`).
3. After the full list is assembled, **filter to current calendar month** by `created_at` prefix `YYYY-MM` (use **UTC** date from `created_at` unless the user specifies another timezone).
4. Commands and a bash loop: [references/github-issues-pagination.md](references/github-issues-pagination.md).

### Step 4: Produce the report

Use the **Report template** below. Fill:

- **Metrics overview** from Step 2c (`buildkite_build_stats.py --markdown`, or with explicit `--from` / `--to`) — place **first** after the title
- **Test content (job scope)** — Content from [references/ci-job-test-scope.md](references/ci-job-test-scope.md) (or user-supplied replacement)
- **Local testing** — Content from [references/local-test-matrix.md](references/local-test-matrix.md) (optional extra bullets for manual spot-check results if the user provides them)
- **CI testing** — Build metadata (number, commit SHA short, branch, time); overall pipeline state (optionally note upload-only failures **separately** from test jobs); summary counts from **reportable jobs** only; failed-job table; per-job pytest table from Step 2b (aggregate + per-failure rows); **### Analysis (CI Failure)** from Step 2d; optional passed major stages
- **Open issues** from Step 3
- **Unknown** if data was incomplete

## Report Template (Markdown)

```markdown
# vLLM-Omni Test Report - Scheduled Nightly

## Metrics overview

(Paste the full `--markdown` output from `scripts/buildkite_build_stats.py` starting at the `## Metrics overview` heading: the Source line and the five-column CI category table including **Success rate/UT coverage**, **Bug avg first response**, **ut**, **ut (exclude models)**, and **bugs (first response, YYYY-MM)**.)

## Test content (job scope)

Paste the Markdown from [references/ci-job-test-scope.md](references/ci-job-test-scope.md) (job names and what each step tests). Update the reference when Buildkite job names change.

## Local testing

Paste the Markdown from the skill reference [references/local-test-matrix.md](references/local-test-matrix.md): *Common stack*, *Test results analysis* (total cases / passed / failed), *Issue tracking* (issue / description / status). Replace if the local matrix differs (user-provided or updated reference file). Optional: add bullets for **manual results** (e.g. spot-check pass/fail) if the user supplies them.

## CI testing (Buildkite — Scheduled nightly)

### Build

| Field | Value |
|-------|--------|
| **Build** | Link: `https://buildkite.com/vllm/vllm-omni/builds/{number}` |
| **Branch** | main |
| **Commit** | short SHA |
| **Trigger** | Scheduled nightly |
| **Started** | ISO time |
| **Finished** | ISO time |
| **Pipeline state** | passed / failed / canceled |
| **Note** | Upload * Pipeline steps omitted from test summaries below |

### Summary (reportable jobs only)

- **Passed**: {n} jobs
- **Failed / broken**: {n} jobs (test executors only)
- **Skipped / blocked**: {n} (if any)

### Failed test jobs (if any)

| Step / Job | State | Notes |
|------------|-------|--------|
| ... | failed | ... |

> Exclude jobs matching `^Upload .+ Pipeline$` unless the user asked for full pipeline ops.

### Per-job test execution (pytest)

| Job | Result | Step link |
|-----|--------|-----------|
| Job A | passed | `https://buildkite.com/vllm/vllm-omni/builds/{n}#{job-id}` |
| Job A — tests/foo.py::test_bar | failed | same |

Rules:

- One **aggregate** row per job when a pytest session summary exists; then one row per **`FAILED` / `ERROR`** node id (node id appended to **Job** after ` — `).
- **Passed** individual tests are **not** listed exhaustively (logs rarely retain every passed node id); open the step log for pytest footer text.
- Non-pytest jobs: single row with **Result** like `state — non-pytest or log truncated` when no pytest footer was found.

### Analysis (CI Failure)

**Filter:** `label:bug`, title prefix **`[CI Failure]`** (**case-insensitive**; rules in [references/ci-github-ci-failure-issues.md](references/ci-github-ci-failure-issues.md)), `created_at` (UTC) in the report month.

**Data sources:** [open `label:bug`](https://github.com/vllm-project/vllm-omni/issues/?q=is%3Aissue%20state%3Aopen%20label%3Abug) · [closed `label:bug`](https://github.com/vllm-project/vllm-omni/issues/?q=is%3Aissue%20state%3Aclosed%20label%3Abug)

| Issue # | Title | Status |
|---------|-------|--------|
| [#xxxx](https://github.com/vllm-project/vllm-omni/issues/xxxx) | … | Open / Closed |

### Passed major stages (optional)

- ...

## Open issues (current month)

| Issue | Title | Opened at | Status | Owner |
|------|-------|-----------|--------|-------|
| [#xxxx](https://github.com/vllm-project/vllm-omni/issues/xxxx) | ... | YYYY-MM-DD | open | @user |

Filter rule (full enumeration, not web UI first page):

- **Data**: all open issues with label `bug`, collected via **API pagination** (Step 3); optionally cross-check [web search](https://github.com/vllm-project/vllm-omni/issues?q=is%3Aissue%20state%3Aopen%20label%3Abug).
- **Keep** only rows where `created_at` falls in the **current month** (compare `YYYY-MM` in UTC from API).
- **Total count** in prose (e.g. "New bugs opened this month: *n*") must match the filtered table length.

## Data source

- Job scope: [references/ci-job-test-scope.md](references/ci-job-test-scope.md)
- Local matrix: [references/local-test-matrix.md](references/local-test-matrix.md)
- Buildkite pipeline: vllm/vllm-omni, branch main
- Build list URL: https://buildkite.com/vllm/vllm-omni/builds?branch=main
- Open bug issues URL: https://github.com/vllm-project/vllm-omni/issues?q=is%3Aissue%20state%3Aopen%20label%3Abug
- `[CI Failure]` issue rules + table: [references/ci-github-ci-failure-issues.md](references/ci-github-ci-failure-issues.md); cross-check [open bugs](https://github.com/vllm-project/vllm-omni/issues/?q=is%3Aissue%20state%3Aopen%20label%3Abug) and [closed bugs](https://github.com/vllm-project/vllm-omni/issues/?q=is%3Aissue%20state%3Aclosed%20label%3Abug)
```

## Constraints

1. **Do not invent** pass/fail counts: use API JSON or user-confirmed paste.
2. If the API returns 401/403, state that **`BUILDKITE_TOKEN` or `BUILDKITE_API_TOKEN` must be set in the environment** (read-only token) and fall back to Option C if the user cannot do that.
3. Prefer **Scheduled nightly** explicitly; do not label a random `main` build as nightly without matching the message/pattern.
4. For **open bugs**, **paginate until done**; do not report "all issues" from a single HTML page.
5. Keep prose concise; tables over long bullet lists.
6. **Always omit** `Upload * Pipeline` jobs from **test** summaries and the per-job pytest table unless the user explicitly requests pipeline upload health.

## Related

- CI pipeline concepts: [vllm-omni-cicd](../vllm-omni-cicd/SKILL.md)
- PR review and test gaps: [vllm-omni-review](../vllm-omni-review/SKILL.md)

## Reference

- Buildkite REST API: [Buildkite API documentation](https://buildkite.com/docs/apis/rest-api)
- Optional detail: [references/buildkite-api.md](references/buildkite-api.md)
- GitHub issues (pagination + month filter): [references/github-issues-pagination.md](references/github-issues-pagination.md)
- CI job test scope (what each nightly job tests): [references/ci-job-test-scope.md](references/ci-job-test-scope.md)
- Local testing (test results analysis / issue tracking / matrix): [references/local-test-matrix.md](references/local-test-matrix.md)
- CI Failure GitHub issues (`[CI Failure]` prefix, case-insensitive; `label:bug`): [references/ci-github-ci-failure-issues.md](references/ci-github-ci-failure-issues.md)

## Cursor copy

A synced copy for editor discovery: `.cursor/skills/vllm-omni-test-report/` - update both when changing this skill.
