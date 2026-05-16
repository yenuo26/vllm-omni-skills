# `nightly_perf_jobs` log layout

## Default path

- `$REPO_ROOT/logs/nightly_perf_jobs` - set **`REPO_ROOT`** to the vLLM-Omni repository root (inside the container if that is where logs are written).

## Discovery rules (used by `scripts/nightly_local_log_report.py`)

1. **Job subdirectories (preferred)**  
   If `LOG_DIR` contains one or more **subdirectories**, each subdirectory name is the **job name**. All `*.log`, `*.out`, and `*.txt` files in that directory are **concatenated** (sorted by name) into one logical log for parsing.

2. **Flat log files**  
   If `LOG_DIR` has **no** subdirectories, each `*.log` / `*.out` / `*.txt` **file** at the top level is treated as **one job**, whose name is the **file stem** (filename without extension).

3. **Hidden files / dirs**  
   Names starting with `.` are ignored.

## Pytest parsing assumptions

- Per-job text should contain pytest output: `FAILED ...`, `ERROR ...`, and preferably a final `===== ... =====` session line listing `N passed`, `N failed`, etc.
- If a job log is truncated before the summary line, counts may be **partial**; the script still lists `FAILED` / `ERROR` nodes and reasons when present.

## When counts disagree

- Prefer the **session summary line** for numeric totals when present.
- If the summary is missing but `FAILED` / `ERROR` lines exist, **failed/error** counts fall back to unique node counts; **passed/total** may be unknown.

## `run_nightly_jobs.sh`

Upstream layout may evolve. If your script writes logs elsewhere, pass `--log-dir` or symlink that directory into `logs/nightly_perf_jobs` for reporting.
