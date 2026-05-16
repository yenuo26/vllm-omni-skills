# Nightly local - cluster & container environment

## `REPO_ROOT`

- Export **`REPO_ROOT`** to the absolute path of the vLLM-Omni repository root **inside the Docker container**, or **`cd`** there before running `run_nightly_jobs.sh`.
- Paths are resolved from the container filesystem; bind-mount your checkout if the image does not include the repo.

## Default log location

- **`$REPO_ROOT/logs/nightly_perf_jobs`** is the default **`LOG_DIR`** for runs and for the report script.
- If `tools/nightly/run_nightly_jobs.sh` writes elsewhere, pass **`--log-dir`** to `nightly_local_log_report.py` or symlink.

## SSH connection name

- The **connection name** is whatever you pass to `ssh`: a **`Host`** entry in `~/.ssh/config` (e.g. `my-hk`) or `user@login.example.com`.
- Use `ssh -v` when diagnosing host key or proxy issues.

## Finding `JOBID` for `--overlap`

- List running jobs: `squeue -u YOUR_USER -t RUNNING` or `squeue -u YOUR_USER -t R`.
- **`srun --jobid=ID --overlap --pty bash`** attaches a new step to an existing allocation; the job must still be **running** and your account must be allowed **`--overlap`**.
- If multiple jobs are running, pick the correct **JOBID**; ask the operator when ambiguous.

## Fallback `srun` (no attach)

When no job id is used:

`srun -p q-fq9hpsac -w hk01dgx006 --gres=gpu:0 --mem-per-cpu=8G --pty  --job-name=ci_local_test`

- Adjust **partition**, **node** (`-w`), **gres**, and **mem** per site policy.

## Docker

- **`docker exec -it <container> bash`** needs access to the Docker socket (or rootless equivalent) on the host where the `srun` step runs.

## `run_nightly_jobs.sh`

- Path: **`tools/nightly/run_nightly_jobs.sh`** relative to the repo root. Forks or branches may differ.
