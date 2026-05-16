---
name: vllm-omni-nightly-local
description: End-to-end HK nightly workflow - SSH with a user-supplied Host name, attach or allocate Slurm (`srun --jobid --overlap` or fallback srun), docker exec into a named container, run tools/nightly/run_nightly_jobs.sh, then parse logs under $REPO_ROOT/logs/nightly_perf_jobs into Markdown with per-job counts and failure reasons. Use when running local/cluster nightly jobs on HK, analyzing nightly_perf_jobs logs, or producing a Markdown test report in one flow.
---

# vLLM-Omni Nightly Local (end-to-end)

## Overview

Single skill, four phases:

1. **Login environment** - SSH, Slurm (`srun` attach or new allocation), Docker.  
2. **Run cases** - `bash tools/nightly/run_nightly_jobs.sh` from **`$REPO_ROOT`**, logs under **`logs/nightly_perf_jobs`**.  
3. **Analyze logs** - Map `LOG_DIR` to jobs and pytest output (see reference).  
4. **Write report** - `scripts/nightly_local_log_report.py` emits Markdown (summary table + failure reasons).

## Required user inputs

Ask before **Step 1** if missing:

| Input | Meaning |
|-------|---------|
| **SSH connection name** | SSH `Host` alias or `user@host` for `ssh`. |
| **Slurm username** | Account for `squeue -u ...` when resolving **JOBID**. |
| **Docker container name** | Target for `docker exec -it ... bash`. |

Optional: **`REPO_ROOT`** path inside the container; **`--log-dir`** if logs are not under the default tree.

---

## 1. Login environment

### 1.1 SSH

```bash
ssh -v "<SSH_CONNECTION_NAME>"
```

Load site modules if needed (e.g. `module load slurm`) before `srun`.

### 1.2 Find JOBID (optional attach)

```bash
SLURM_USER="<username>"
squeue -u "$SLURM_USER" -t RUNNING -h -o "%i"
```

- Use **RUNNING** jobs for `--overlap`. If several IDs appear, **confirm** which **JOBID** with the user.
- If a suitable **JOBID** exists:

```bash
JOBID="<chosen_jobid>"
srun --jobid="$JOBID" --overlap --pty bash
```

### 1.3 New allocation (no attach)

If **no** suitable running job (or user declines attach):

```bash
srun -p q-fq9hpsac -w hk01dgx006 --gres=gpu:0 --mem-per-cpu=8G --pty  --job-name=ci_local_test
```

### 1.4 Enter container

```bash
docker exec -it "<CONTAINER_NAME>" bash
```

More context: [references/nightly-local-environment.md](references/nightly-local-environment.md).

---

## 2. Run test cases

Inside the container, from the **vLLM-Omni** repo root:

```bash
export REPO_ROOT=/path/to/vllm-omni   # or cd there
bash tools/nightly/run_nightly_jobs.sh
```

Default log directory:

```bash
LOG_DIR="$REPO_ROOT/logs/nightly_perf_jobs"
```

Confirm new or updated files under **`LOG_DIR`** when the script finishes.

---

## 3. Analyze logs

- How paths map to **jobs** and pytest expectations: [references/nightly-local-log-layout.md](references/nightly-local-log-layout.md).
- List **`LOG_DIR`**; if layout differs from the reference, use **`--log-dir`** when generating the report or reorganize files.

---

## 4. Produce Markdown report

**On a machine that can read `LOG_DIR`** (often: copy logs out, or run inside the same container/filesystem):

```bash
export REPO_ROOT=/path/to/vllm-omni
python scripts/nightly_local_log_report.py --markdown-report /tmp/nightly-report.md
# or stdout:
python scripts/nightly_local_log_report.py
```

Options: `--log-dir`, `--repo-root`, `--title`. See `python scripts/nightly_local_log_report.py --help`.

### Report contents

| Section | Content |
|--------|---------|
| **Meta** | Timestamp (UTC), `$REPO_ROOT`, `LOG_DIR`, git commit if available |
| **Summary** | One row per **job**: totals, passed, failed, skipped, errors, pytest summary line |
| **Failures** | Per node: **reason** (`FAILED`/`ERROR` line after ` - `, or following `E   ...`) |

---

## Agent workflow

1. Collect **SSH connection name**, **Slurm username**, **Docker container name**; do not guess **JOBID** when multiple allocations exist.
2. Walk **Section 1** (SSH -> squeue -> 1.2 or 1.3 -> docker exec).
3. In the container: **Section 2** - ensure **`REPO_ROOT`**, run **`run_nightly_jobs.sh`**, verify **`LOG_DIR`**.
4. **Section 3** - align disk layout with [references/nightly-local-log-layout.md](references/nightly-local-log-layout.md).
5. **Section 4** - run **`nightly_local_log_report.py`**; add human context (hardware, branch, env) to the Markdown if needed.
6. If logs are not pytest-shaped, say so and paste trailing log lines for triage.

## References

- Cluster, Slurm overlap, Docker, `REPO_ROOT`: [references/nightly-local-environment.md](references/nightly-local-environment.md)
- Log tree and pytest parsing rules: [references/nightly-local-log-layout.md](references/nightly-local-log-layout.md)
