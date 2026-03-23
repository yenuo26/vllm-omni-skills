# Buildkite API Notes (vllm-omni)

## Endpoints

| Purpose | Method | Path |
|---------|--------|------|
| List builds | GET | `/v2/organizations/vllm/pipelines/vllm-omni/builds` |
| Single build | GET | `/v2/organizations/vllm/pipelines/vllm-omni/builds/{number}` |

Query params for list: `branch=main`, `per_page=30` (max 100 per Buildkite docs).

## Authentication

Put a read-only Buildkite API token in the environment as **`BUILDKITE_TOKEN`** or **`BUILDKITE_API_TOKEN`**. HTTP header: `Authorization: Bearer` + that value (e.g. in bash: `-H "Authorization: Bearer $BUILDKITE_TOKEN"` when `BUILDKITE_TOKEN` is set).

**Do not** commit tokens or pass them on the command line as literal arguments; keep them in shell env or CI secrets only.

Without a credential, the REST API typically returns **401**. The public web UI at [buildkite.com/vllm/vllm-omni/builds?branch=main](https://buildkite.com/vllm/vllm-omni/builds?branch=main) is for humans; automated report generation should use the API with an env-sourced token.

## Identifying scheduled nightly builds

Scheduled builds usually have `message` like:

- `Scheduled nightly build`

Filter client-side after fetching `builds[]`:

```text
builds | map(select(.message | test("Scheduled nightly"; "i")))
```

Take index `0` for the latest if the API returns builds newest-first (default).

## Useful JSON fields (build object)

- `number`, `state`, `branch`, `commit`, `message`, `created_at`, `finished_at`
- `jobs[]`: each job has `name`, `state`, `id` (for deep links), `log_url`, `raw_log_url`

## Job logs (pytest detail)

Each job may include:

- `raw_log_url` - plain-text log (preferred for parsing)
- `log_url` - formatted log API URL

Fetch with the same `Authorization: Bearer` header as other REST calls (value from `BUILDKITE_TOKEN` or `BUILDKITE_API_TOKEN`).

Very large logs: keep a **tail window** (pytest prints the session summary at the end). The helper script
[`scripts/nightly_job_pytest_table.py`](../scripts/nightly_job_pytest_table.py) downloads the full log but,
if it grows beyond an internal cap, retains only the last ~10 MiB so the session footer remains available.

## Jobs excluded from test reporting

**Do not** include the following in job counts, failure lists, or the per-job pytest table:

- Any job whose **name** matches `(?i)^Upload .+ Pipeline$`
  (e.g. `Upload Ready Pipeline`, `Upload Nightly Pipeline`, `Upload Merge Pipeline`)

These steps are **artifact/metadata uploads**, not test executors. The overall Buildkite build `state` may still
reflect them; prose should clarify that **test health** is evaluated on the remaining jobs only.

## Per-job test case table (Markdown)

When filling the report's **Per-job test execution (pytest)** section:

1. Iterate **reportable jobs** only (after the Upload filter above).
2. For each job, pull `raw_log_url` and parse pytest output:
   - **Aggregate row**: scope `(pytest aggregate)`, `Detail` = final `=== ... ===` session line when present.
   - **Failure / error rows**: one row per `FAILED ...` / `ERROR ...` node id line pytest prints (dedupe repeats).
3. **Do not invent** node ids or counts: if the log was truncated and no `FAILED` lines appear but the
   aggregate shows failures, state `Detail` as "log truncated; open step log in UI".
4. Non-pytest jobs (Docker build, email, init): a single row with scope `(non-pytest or log truncated)` and
   `Detail` explaining that no pytest session line was found.

## CI aggregate stats (`buildkite_build_stats.py`)

The script [scripts/buildkite_build_stats.py](../scripts/buildkite_build_stats.py) pages through **all builds** in a
`created_from` / `created_to` window (UTC, Buildkite query params) and buckets each finished build into:

| Bucket | Rule |
|--------|------|
| ready | `branch != "main"` |
| merge | `branch == "main"` and (`source == "schedule"` or message suggests scheduled/nightly) |
| nightly | `branch == "main"` and not nightly |

**Success rate** (per bucket): `passed / (passed + failed)` only. Counts of `canceled`, `blocked`, etc. are reported separately.

**Average wall time** (per bucket): among builds counted as `passed` or `failed`, those with both `created_at` and
`finished_at`, compute `finished_at - created_at` in seconds and take the arithmetic mean.

Run with `BUILDKITE_TOKEN` or `BUILDKITE_API_TOKEN` and optional `--markdown` for a report-ready **CI details** table.

## Example: jq one-liner for latest scheduled nightly number

```bash
curl -s -H "Authorization: Bearer $BUILDKITE_TOKEN" \
  "https://api.buildkite.com/v2/organizations/vllm/pipelines/vllm-omni/builds?branch=main&per_page=50" \
  | jq '[.[] | select(.message | test("Scheduled nightly"; "i"))] | .[0].number'
```
