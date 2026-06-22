#!/usr/bin/env python3
"""
Archive a generated HTML test report into vllm-omni-kanban and stage for push.

Copies the report into ``data/nightly_test_report/`` or ``data/release_test_report/``
(with kanban-expected filenames). **Do not commit** ``docs/assets/test_reports/`` — that
tree is gitignored in kanban; ``mkdocs build`` / ``mkdocs serve`` regenerates it from
``data/`` via ``scripts/mkdocs_hooks.py`` → ``sync_test_reports.py``.

Then ``git pull --rebase``, ``git add`` (data HTML only), and print a **push preview**.
This script does **not** commit or push. After reviewing the preview, run
``push_kanban_report.py`` separately (it prompts for confirmation before ``git push``).

Uses **GitHub CLI (``gh``)** credentials for pull (``gh auth git-credential``).
Requires ``gh`` installed and authenticated (``gh auth login`` or ``GH_TOKEN`` / ``GITHUB_TOKEN``).

Default remote repo: https://github.com/hsliuustc0106/vllm-omni-kanban

Run from the skill directory after generating a report::

  python scripts/push_report_to_kanban.py \\
    --report ./nightly-report-buildkite-latest-2026-06-22.html \\
    --kanban-repo-root /path/to/vllm-omni-kanban \\
    --kind nightly

  python scripts/push_kanban_report.py \\
    --kanban-repo-root /path/to/vllm-omni-kanban
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from shutil import copy2

KANBAN_REPO_URL = "https://github.com/hsliuustc0106/vllm-omni-kanban"
KANBAN_REPO_GIT_SUFFIX = "vllm-omni-kanban"
GH_CLI_INSTALL_HINT = (
    "GitHub CLI (gh) 未安装。归档 push 需要先安装 gh：\n"
    "  Windows: winget install --id GitHub.cli\n"
    "  macOS:   brew install gh\n"
    "  Linux:   https://github.com/cli/cli/blob/trunk/docs/install_linux.md\n"
    "安装后登录: gh auth login\n"
    "文档: https://cli.github.com/"
)
GH_AUTH_HINT = (
    "gh 未登录或 token 无效。请运行: gh auth login\n"
    "或在环境中设置 GH_TOKEN / GITHUB_TOKEN（需 repo 权限）。"
)
GH_GIT_CREDENTIAL_HELPER = "!gh auth git-credential"

NIGHTLY_CANONICAL_RE = re.compile(
    r"^nightly-report-buildkite-latest-(?P<date>\d{4}-\d{2}-\d{2})\.html$",
    re.IGNORECASE,
)
RELEASE_CANONICAL_RE = re.compile(
    r"^vllm-omni-release-test-report-(?P<date>\d{4}-\d{2}-\d{2})\.html$",
    re.IGNORECASE,
)
RELEASE_LOOSE_RE = re.compile(
    r"^vllm-omni-test-report(?:-preview)?-(?P<date>\d{4}-\d{2}-\d{2})\.html$",
    re.IGNORECASE,
)
DATE_IN_NAME_RE = re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})")


@dataclass(frozen=True)
class ArchivePlan:
    kind: str  # "nightly" | "release"
    report_date: str  # YYYY-MM-DD
    dest_name: str
    dest_rel: Path  # relative to kanban repo root


@dataclass(frozen=True)
class PushPreview:
    """Staged changes ready to commit and push."""

    plan: ArchivePlan
    kanban_repo: Path
    remote: str
    remote_url: str
    branch: str
    commit_message: str
    paths: list[str]
    name_status: str
    diff_stat: str
    file_details: list[str]


class GhCliRequiredError(RuntimeError):
    """Raised when gh is missing or not authenticated for push."""


class PushCancelledError(RuntimeError):
    """User declined push after reviewing the preview."""


class PushConfirmationRequiredError(RuntimeError):
    """Non-interactive session: preview printed; user must confirm via push_kanban_report.py."""

    def __init__(self, preview: PushPreview) -> None:
        self.preview = preview
        super().__init__(
            "Push preview shown. After the user confirms in chat, run:\n"
            "  python scripts/push_kanban_report.py --kanban-repo-root <path> --yes"
        )


def _gh_cli_path() -> str | None:
    return shutil.which("gh")


def ensure_gh_cli() -> None:
    if _gh_cli_path() is None:
        raise GhCliRequiredError(GH_CLI_INSTALL_HINT)


def ensure_gh_authenticated() -> None:
    ensure_gh_cli()
    proc = _run_gh("auth", "status", check=False)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        msg = GH_AUTH_HINT
        if detail:
            msg = f"{GH_AUTH_HINT}\n{detail}"
        raise GhCliRequiredError(msg)


def _run_git(
    repo: Path,
    *args: str,
    check: bool = True,
    gh_credential: bool = False,
) -> subprocess.CompletedProcess[str]:
    cmd = ["git"]
    if gh_credential:
        cmd.extend(["-c", f"credential.helper={GH_GIT_CREDENTIAL_HELPER}"])
    cmd.extend(args)
    proc = subprocess.run(
        cmd,
        cwd=str(repo),
        text=True,
        capture_output=True,
        check=False,
    )
    if check and proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"{' '.join(cmd)} failed: {detail}")
    return proc


def _run_gh(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    ensure_gh_cli()
    proc = subprocess.run(
        ["gh", *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if check and proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"gh {' '.join(args)} failed: {detail}")
    return proc


def _git_current_branch(repo: Path) -> str:
    proc = _run_git(repo, "branch", "--show-current")
    branch = (proc.stdout or "").strip()
    if not branch:
        raise RuntimeError(f"Unable to determine current branch in {repo}")
    return branch


def _git_remote_url(repo: Path, remote: str) -> str:
    proc = _run_git(repo, "remote", "get-url", remote, check=False)
    if proc.returncode != 0:
        return ""
    return (proc.stdout or "").strip()


def infer_report_kind_and_date(
    report_path: Path,
    *,
    kind: str | None = None,
    report_date: str | None = None,
) -> tuple[str, str]:
    name = report_path.name
    if kind is None:
        if NIGHTLY_CANONICAL_RE.match(name) or name.lower().startswith("nightly"):
            kind = "nightly"
        elif RELEASE_CANONICAL_RE.match(name) or RELEASE_LOOSE_RE.match(name):
            kind = "release"
        else:
            kind = "nightly" if "nightly" in name.lower() else "release"
    kind = kind.lower()
    if kind not in ("nightly", "release"):
        raise ValueError(f"Unsupported report kind: {kind!r}")

    if report_date:
        return kind, report_date

    for pattern in (NIGHTLY_CANONICAL_RE, RELEASE_CANONICAL_RE, RELEASE_LOOSE_RE):
        match = pattern.match(name)
        if match:
            return kind, match.group("date")

    dates = DATE_IN_NAME_RE.findall(name)
    if dates:
        return kind, dates[-1]

    return kind, datetime.now(timezone.utc).date().isoformat()


def build_archive_plan(
    report_path: Path,
    *,
    kind: str | None = None,
    report_date: str | None = None,
) -> ArchivePlan:
    resolved_kind, resolved_date = infer_report_kind_and_date(
        report_path,
        kind=kind,
        report_date=report_date,
    )
    if resolved_kind == "nightly":
        dest_name = f"nightly-report-buildkite-latest-{resolved_date}.html"
        dest_rel = Path("data") / "nightly_test_report" / dest_name
    else:
        dest_name = f"vllm-omni-release-test-report-{resolved_date}.html"
        dest_rel = Path("data") / "release_test_report" / dest_name
    return ArchivePlan(
        kind=resolved_kind,
        report_date=resolved_date,
        dest_name=dest_name,
        dest_rel=dest_rel,
    )


def archive_report_to_kanban(
    report_path: Path,
    kanban_repo: Path,
    *,
    kind: str | None = None,
    report_date: str | None = None,
) -> ArchivePlan:
    report_path = report_path.resolve()
    kanban_repo = kanban_repo.resolve()
    if not report_path.is_file():
        raise FileNotFoundError(f"Report not found: {report_path}")
    if not kanban_repo.is_dir():
        raise NotADirectoryError(f"Kanban repo root not found: {kanban_repo}")

    plan = build_archive_plan(report_path, kind=kind, report_date=report_date)
    dest = kanban_repo / plan.dest_rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    copy2(report_path, dest)
    return plan


def _git_paths_for_plan(plan: ArchivePlan) -> list[str]:
    """Only ``data/*_test_report/*.html`` is tracked; ``docs/assets/test_reports/`` is gitignored."""
    return [str(plan.dest_rel).replace("\\", "/")]


def _format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KiB"
    return f"{size / (1024 * 1024):.1f} MiB"


def _staged_report_rel_paths(kanban_repo: Path) -> list[str]:
    proc = _run_git(
        kanban_repo,
        "diff",
        "--cached",
        "--name-only",
        check=False,
    )
    paths: list[str] = []
    for raw in (proc.stdout or "").splitlines():
        rel = raw.strip().replace("\\", "/")
        if rel.startswith("data/nightly_test_report/") or rel.startswith(
            "data/release_test_report/"
        ):
            paths.append(rel)
    return paths


def infer_plan_from_staged_rel(rel: str) -> ArchivePlan:
    rel = rel.replace("\\", "/")
    name = Path(rel).name
    if "nightly_test_report" in rel:
        match = NIGHTLY_CANONICAL_RE.match(name)
        if match:
            report_date = match.group("date")
        else:
            dates = DATE_IN_NAME_RE.findall(name)
            report_date = (
                dates[-1] if dates else datetime.now(timezone.utc).date().isoformat()
            )
        return ArchivePlan(
            kind="nightly",
            report_date=report_date,
            dest_name=name,
            dest_rel=Path(rel),
        )

    match = RELEASE_CANONICAL_RE.match(name) or RELEASE_LOOSE_RE.match(name)
    if match:
        report_date = match.group("date")
    else:
        dates = DATE_IN_NAME_RE.findall(name)
        report_date = (
            dates[-1] if dates else datetime.now(timezone.utc).date().isoformat()
        )
    return ArchivePlan(
        kind="release",
        report_date=report_date,
        dest_name=name,
        dest_rel=Path(rel),
    )


def build_push_preview_from_staged(
    kanban_repo: Path,
    *,
    remote: str = "origin",
    branch: str | None = None,
    commit_message: str | None = None,
) -> PushPreview | None:
    kanban_repo = kanban_repo.resolve()
    staged = _staged_report_rel_paths(kanban_repo)
    if not staged:
        return None

    plan = infer_plan_from_staged_rel(staged[0])
    branch = branch or _git_current_branch(kanban_repo)
    commit_message = commit_message or (
        f"chore(reports): archive {plan.kind} test report {plan.report_date}"
    )
    return _build_push_preview(
        kanban_repo,
        plan,
        remote=remote,
        branch=branch,
        commit_message=commit_message,
        paths=staged,
    )


def _staged_file_details(kanban_repo: Path) -> list[str]:
    proc = _run_git(
        kanban_repo,
        "diff",
        "--cached",
        "--name-only",
        check=False,
    )
    lines: list[str] = []
    for raw in (proc.stdout or "").splitlines():
        rel = raw.strip()
        if not rel:
            continue
        path = kanban_repo / rel
        if path.is_file():
            size = _format_bytes(path.stat().st_size)
            lines.append(f"  {rel}  ({size})")
        else:
            lines.append(f"  {rel}")
    return lines


def _build_push_preview(
    kanban_repo: Path,
    plan: ArchivePlan,
    *,
    remote: str,
    branch: str,
    commit_message: str,
    paths: list[str],
) -> PushPreview:
    name_status_proc = _run_git(
        kanban_repo,
        "diff",
        "--cached",
        "--name-status",
        check=False,
    )
    diff_stat_proc = _run_git(
        kanban_repo,
        "diff",
        "--cached",
        "--stat",
        check=False,
    )
    return PushPreview(
        plan=plan,
        kanban_repo=kanban_repo,
        remote=remote,
        remote_url=_git_remote_url(kanban_repo, remote),
        branch=branch,
        commit_message=commit_message,
        paths=paths,
        name_status=(name_status_proc.stdout or "").strip() or "(no staged diff)",
        diff_stat=(diff_stat_proc.stdout or "").strip() or "(no diff stat)",
        file_details=_staged_file_details(kanban_repo),
    )


def format_push_preview(preview: PushPreview) -> str:
    lines = [
        "",
        "=" * 60,
        "Kanban push preview",
        "=" * 60,
        f"Repository : {preview.kanban_repo}",
        f"Remote     : {preview.remote}"
        + (f" -> {preview.remote_url}" if preview.remote_url else ""),
        f"Branch     : {preview.branch}",
        f"Target     : {KANBAN_REPO_URL}",
        f"Report kind: {preview.plan.kind}",
        f"Report date: {preview.plan.report_date}",
        f"Archive    : {preview.plan.dest_rel.as_posix()} (only this path is committed)",
        f"Note       : docs/assets/test_reports/ is gitignored; MkDocs syncs from data/ at build",
        f"Commit msg : {preview.commit_message}",
        "",
        "Staged files:",
    ]
    if preview.file_details:
        lines.extend(preview.file_details)
    else:
        lines.append("  (none)")
    lines.extend(
        [
            "",
            "Name-status (staged):",
            preview.name_status,
            "",
            "Diff stat (staged):",
            preview.diff_stat,
            "=" * 60,
        ]
    )
    return "\n".join(lines)


def _unstage_paths(kanban_repo: Path, paths: list[str]) -> None:
    _run_git(kanban_repo, "restore", "--staged", *paths, check=False)


def _confirm_push(preview: PushPreview, *, assume_yes: bool) -> None:
    print(format_push_preview(preview), flush=True)
    if assume_yes:
        print("Push confirmed via --yes.", flush=True)
        return
    if sys.stdin.isatty():
        try:
            answer = input(
                "\nProceed with git commit and push to kanban? [y/N]: "
            ).strip().lower()
        except EOFError:
            answer = ""
        if answer in ("y", "yes"):
            return
        _unstage_paths(preview.kanban_repo, preview.paths)
        raise PushCancelledError("Push cancelled by user.")

    _unstage_paths(preview.kanban_repo, preview.paths)
    raise PushConfirmationRequiredError(preview)


def _prepare_staged_push(
    kanban_repo: Path,
    plan: ArchivePlan,
    *,
    remote: str,
    branch: str | None,
    commit_message: str | None,
    skip_pull: bool,
) -> PushPreview | None:
    kanban_repo = kanban_repo.resolve()
    if not (kanban_repo / ".git").exists():
        raise RuntimeError(f"Not a git repository: {kanban_repo}")

    remote_url = _git_remote_url(kanban_repo, remote)
    if remote_url and KANBAN_REPO_GIT_SUFFIX not in remote_url:
        print(
            f"Warning: remote {remote!r} URL {remote_url!r} does not look like vllm-omni-kanban.",
            file=sys.stderr,
        )

    branch = branch or _git_current_branch(kanban_repo)
    commit_message = commit_message or (
        f"chore(reports): archive {plan.kind} test report {plan.report_date}"
    )
    paths = _git_paths_for_plan(plan)

    ensure_gh_authenticated()

    if not skip_pull:
        pull = _run_git(
            kanban_repo,
            "pull",
            "--rebase",
            remote,
            branch,
            check=False,
            gh_credential=True,
        )
        if pull.returncode != 0:
            detail = (pull.stderr or pull.stdout or "").strip()
            raise RuntimeError(
                f"git pull --rebase {remote} {branch} failed: {detail}"
            )

    _run_git(kanban_repo, "add", *paths)
    status = _run_git(kanban_repo, "status", "--porcelain", *paths, check=False)
    if not (status.stdout or "").strip():
        return None

    return _build_push_preview(
        kanban_repo,
        plan,
        remote=remote,
        branch=branch,
        commit_message=commit_message,
        paths=paths,
    )


def commit_and_push_staged(
    preview: PushPreview,
    *,
    dry_run: bool = False,
) -> str:
    if dry_run:
        return (
            f"[dry-run] would git commit -m {preview.commit_message!r}; "
            f"git push {preview.remote} {preview.branch} (gh credential)"
        )

    ensure_gh_authenticated()
    _run_git(
        preview.kanban_repo,
        "-c",
        "user.name=vllm-omni-test-report",
        "-c",
        "user.email=vllm-omni-test-report@users.noreply.github.com",
        "commit",
        "-m",
        preview.commit_message,
    )
    push = _run_git(
        preview.kanban_repo,
        "push",
        preview.remote,
        preview.branch,
        check=False,
        gh_credential=True,
    )
    if push.returncode != 0:
        detail = (push.stderr or push.stdout or "").strip()
        raise RuntimeError(
            f"git push {preview.remote} {preview.branch} failed "
            f"(via gh credentials): {detail}"
        )
    return (
        f"Pushed {preview.plan.kind} report {preview.plan.report_date} to "
        f"{preview.remote}/{preview.branch} ({KANBAN_REPO_URL}) using gh CLI credentials."
    )


def prepare_report_for_kanban(
    report_path: Path,
    kanban_repo: Path,
    *,
    kind: str | None = None,
    report_date: str | None = None,
    remote: str = "origin",
    branch: str | None = None,
    commit_message: str | None = None,
    dry_run: bool = False,
    archive_only: bool = False,
    skip_pull: bool = False,
) -> tuple[ArchivePlan, str]:
    plan = archive_report_to_kanban(
        report_path,
        kanban_repo,
        kind=kind,
        report_date=report_date,
    )
    if archive_only:
        return plan, f"Archived to {kanban_repo / plan.dest_rel} (no git staging)."

    paths = _git_paths_for_plan(plan)
    branch = branch or _git_current_branch(kanban_repo.resolve())
    commit_message = commit_message or (
        f"chore(reports): archive {plan.kind} test report {plan.report_date}"
    )

    if dry_run:
        return plan, (
            f"[dry-run] would verify gh CLI + gh auth status; "
            f"git -C {kanban_repo} pull --rebase {remote} {branch} (gh credential); "
            f"git add {' '.join(paths)}; show push preview; "
            f"then run push_kanban_report.py to confirm, commit, and push"
        )

    preview = _prepare_staged_push(
        kanban_repo,
        plan,
        remote=remote,
        branch=branch,
        commit_message=commit_message,
        skip_pull=skip_pull,
    )
    if preview is None:
        return plan, f"No git changes under {', '.join(paths)}; kanban already up to date."

    print(format_push_preview(preview), flush=True)
    return plan, (
        "Staged for commit. Review the preview above.\n"
        "After confirming, run:\n"
        "  python scripts/push_kanban_report.py "
        f"--kanban-repo-root {kanban_repo.resolve()}"
    )


def _default_kanban_repo() -> Path | None:
    env = (os.environ.get("KANBAN_REPO_ROOT") or "").strip()
    return Path(env).resolve() if env else None


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Copy an HTML test report into vllm-omni-kanban data/, stage it, "
            "and print a push preview (does not commit or push)."
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        required=True,
        help="Path to the generated HTML report file.",
    )
    parser.add_argument(
        "--kanban-repo-root",
        type=Path,
        default=_default_kanban_repo(),
        help=(
            "Local checkout of vllm-omni-kanban "
            f"({KANBAN_REPO_URL}). Default: $KANBAN_REPO_ROOT."
        ),
    )
    parser.add_argument(
        "--kind",
        choices=("nightly", "release"),
        default=None,
        help="Report type (default: infer from filename).",
    )
    parser.add_argument(
        "--date",
        dest="report_date",
        default=None,
        help="Report date YYYY-MM-DD (default: parse from filename or UTC today).",
    )
    parser.add_argument(
        "--remote",
        default="origin",
        help="Git remote name (default: origin).",
    )
    parser.add_argument(
        "--branch",
        default=None,
        help="Git branch to push (default: current branch).",
    )
    parser.add_argument(
        "--commit-message",
        default=None,
        help="Custom git commit message.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned git actions without commit/push.",
    )
    parser.add_argument(
        "--archive-only",
        action="store_true",
        help="Copy into kanban data/ only; do not stage or push.",
    )
    parser.add_argument(
        "--skip-pull",
        action="store_true",
        help="Skip git pull --rebase before staging (not recommended).",
    )
    args = parser.parse_args()

    if args.kanban_repo_root is None:
        print(
            "Set --kanban-repo-root or export KANBAN_REPO_ROOT "
            f"to a local clone of {KANBAN_REPO_URL}.",
            file=sys.stderr,
        )
        sys.exit(2)

    try:
        plan, note = prepare_report_for_kanban(
            args.report,
            args.kanban_repo_root,
            kind=args.kind,
            report_date=args.report_date,
            remote=args.remote,
            branch=args.branch,
            commit_message=args.commit_message,
            dry_run=args.dry_run,
            archive_only=args.archive_only,
            skip_pull=args.skip_pull,
        )
    except (FileNotFoundError, NotADirectoryError, RuntimeError, ValueError, GhCliRequiredError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    print(f"Archived {args.report} -> {args.kanban_repo_root / plan.dest_rel}")
    print(note)


if __name__ == "__main__":
    main()
