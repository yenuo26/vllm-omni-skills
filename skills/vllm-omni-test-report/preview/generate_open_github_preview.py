#!/usr/bin/env python3
"""Generate a static HTML preview for File issue / Open GitHub button testing."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Preview uses fork with issue-form ids until vllm-project/vllm-omni merges the template PR.
os.environ.setdefault(
    "VLLM_OMNI_ISSUE_REPO", "https://github.com/yenuo26/vllm-omni"
)

_PREVIEW = Path(__file__).resolve().parent
_SCRIPTS = _PREVIEW.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from nightly_job_pytest_table import extract_ci_versions_from_log, job_anchor  # noqa: E402
from nightly_local_log_report import (  # noqa: E402
    KanbanAssetsConfig,
    LocalPerfResultConfig,
    emit_report_html,
)
from pytest_log_parse import parse_pytest_log  # noqa: E402


def _mock_buildkite_jobs(ci_log: str) -> tuple[dict, list[dict]]:
    build = {
        "number": 9999,
        "state": "failed",
        "message": "[PREVIEW] Mock Buildkite nightly — Open GitHub button demo",
        "commit": "a1b2c3d4e5f6789012345678",
        "jobs": [],
    }
    job_id = "preview-job-omni-function"
    ci_log_parsed = parse_pytest_log(ci_log)
    rec = {
        "name": ":pytest: Omni Function Test with H100",
        "state": "failed",
        "step_link": job_anchor(9999, job_id),
        "raw_url": "preview://mock",
        "info": ci_log_parsed,
        "log_error": None,
        "build_commit_short": "a1b2c3d4e5f6",
        "ci_versions": extract_ci_versions_from_log(ci_log),
    }
    return build, [rec]


def main() -> None:
    log_dir = _PREVIEW / "sample-logs"
    ci_log = (_PREVIEW / "ci_mock_step.log").read_text(encoding="utf-8")
    bk_build, bk_jobs = _mock_buildkite_jobs(ci_log)
    out = _PREVIEW / "open-github-button-preview.html"
    repo_root = _PREVIEW.parent

    with out.open("w", encoding="utf-8") as fp:
        emit_report_html(
            title="Open GitHub 按钮预览 — Local + Buildkite 失败分析",
            repo_root=repo_root,
            log_dir=log_dir,
            out_fp=fp,
            bk_build=bk_build,
            bk_jobs=bk_jobs,
            bk_note=None,
            kanban_cfg=KanbanAssetsConfig(assets_dir=None, repo_root=None),
            local_perf_cfg=LocalPerfResultConfig(result_root=None),
        )
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
