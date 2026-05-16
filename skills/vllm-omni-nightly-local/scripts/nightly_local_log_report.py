#!/usr/bin/env python3
"""
Parse pytest-style logs under logs/nightly_perf_jobs (or --log-dir) and emit Markdown.

Discovery: see ../references/nightly-local-log-layout.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path
from typing import Any

# Pytest final session lines (6.x/7.x/8.x variants).
SESSION_LINE_RE = re.compile(r"^=+\s*.+\s*in\s+[\d.]+s\s*=+\s*$")
COUNTS_FRAGMENT_RE = re.compile(
    r"(\d+)\s+passed|(\d+)\s+failed|(\d+)\s+skipped|(\d+)\s+errors?\b",
    re.IGNORECASE,
)


def _md_cell(s: str) -> str:
    return (s or "").replace("|", "/").replace("\n", " ")


def render_markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    cols = len(headers)
    if not headers:
        return ""
    for row in rows:
        if len(row) != cols:
            raise ValueError(f"row has {len(row)} cells, expected {cols}: {row!r}")
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * cols) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _reason_from_failed_line(node_line: str, lines: list[str], idx: int) -> str:
    if " - " in node_line:
        return node_line.split(" - ", 1)[1].strip()
    for j in range(idx + 1, min(idx + 8, len(lines))):
        s = lines[j].strip()
        if not s:
            continue
        if s.startswith("E   "):
            return s[4:].strip()
        if s.startswith("E       "):
            return s[8:].strip()
        if re.match(r"^(AssertionError|ValueError|RuntimeError|TypeError|KeyError)\b", s):
            return s
    return "(no inline reason; see log)"


def parse_pytest(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    failed_nodes: list[str] = []
    error_nodes: list[str] = []
    failed_reasons: dict[str, str] = {}
    error_reasons: dict[str, str] = {}

    for i, line in enumerate(lines):
        if line.startswith("FAILED "):
            rest = line[7:].strip()
            failed_nodes.append(rest)
            failed_reasons[rest] = _reason_from_failed_line(rest, lines, i)
        elif line.startswith("ERROR "):
            rest = line[6:].strip()
            error_nodes.append(rest)
            error_reasons[rest] = _reason_from_failed_line(rest, lines, i)

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

    def dedupe(seq: list[str]) -> list[str]:
        return list(dict.fromkeys(seq))

    failed_nodes = dedupe(failed_nodes)
    error_nodes = dedupe(error_nodes)
    return {
        "failed_nodes": failed_nodes,
        "error_nodes": error_nodes,
        "failed_reasons": {k: failed_reasons[k] for k in failed_nodes},
        "error_reasons": {k: error_reasons[k] for k in error_nodes},
        "summary": summary,
    }


def extract_pytest_counts(summary: str | None) -> dict[str, int]:
    out = {"passed": 0, "failed": 0, "skipped": 0, "error": 0}
    if not summary:
        return out
    low = summary.lower()
    for m in re.finditer(
        r"(\d+)\s+(passed|failed|skipped|errors?)\b",
        low,
    ):
        n = int(m.group(1))
        kind = m.group(2)
        if kind == "passed":
            out["passed"] = n
        elif kind == "failed":
            out["failed"] = n
        elif kind == "skipped":
            out["skipped"] = n
        elif kind == "error" or kind == "errors":
            out["error"] = n
    return out


def default_log_dir(repo_root: Path) -> Path:
    return repo_root / "logs" / "nightly_perf_jobs"


def discover_job_logs(log_dir: Path) -> list[tuple[str, list[Path]]]:
    if not log_dir.is_dir():
        return []
    subs = sorted(
        [p for p in log_dir.iterdir() if not p.name.startswith(".")],
        key=lambda p: p.name,
    )
    if not subs:
        return []

    dirs = [p for p in subs if p.is_dir()]
    if dirs:
        groups: list[tuple[str, list[Path]]] = []
        for d in sorted(dirs, key=lambda p: p.name):
            resolved: list[Path] = []
            for pat in ("*.log", "*.out", "*.txt"):
                resolved.extend(sorted(d.glob(pat)))
            if resolved:
                groups.append((d.name, resolved))
        return groups

    files: list[Path] = []
    for p in subs:
        if not p.is_file():
            continue
        if p.suffix.lower() not in (".log", ".out", ".txt"):
            continue
        files.append(p)
    files.sort(key=lambda p: p.name)
    return [(p.stem, [p]) for p in files]


def read_job_text(paths: list[Path]) -> str:
    chunks: list[str] = []
    for p in paths:
        try:
            chunks.append(p.read_text(encoding="utf-8-sig", errors="replace"))
        except OSError as e:
            chunks.append(f"\n<<< read error {p}: {e} >>>\n")
    return "\n".join(chunks)


def emit_report(
    *,
    title: str,
    repo_root: Path,
    log_dir: Path,
    out_fp: Any,
) -> None:
    groups = discover_job_logs(log_dir)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = [
        f"# {_md_cell(title)}",
        "",
        f"- **Generated:** {now}",
        f"- **REPO_ROOT:** `{repo_root}`",
        f"- **LOG_DIR:** `{log_dir}`",
        "",
    ]

    if not groups:
        lines.append("## Summary")
        lines.append("")
        lines.append(
            f"*No job logs found under `{log_dir}`. "
            "Confirm nightly jobs ran and paths match "
            "[references/nightly-local-log-layout.md](references/nightly-local-log-layout.md).*"
        )
        print("\n".join(lines), file=out_fp)
        return

    summary_rows: list[list[str]] = []

    for job_name, paths in groups:
        text = read_job_text(paths)
        info = parse_pytest(text)
        counts = extract_pytest_counts(info["summary"])
        n_fail = len(info["failed_nodes"])
        n_err = len(info["error_nodes"])

        if info["summary"] is None and not info["failed_nodes"] and not n_err:
            total = ""
            ok = ""
            bad = ""
            skip = ""
            errc = ""
        else:
            fc = counts["failed"] if counts["failed"] else n_fail
            ec = counts["error"] if counts["error"] else n_err
            if counts["passed"] or counts["failed"] or counts["skipped"] or counts["error"]:
                total = str(
                    counts["passed"] + counts["failed"] + counts["skipped"] + counts["error"]
                )
                ok = str(counts["passed"])
                bad = str(fc)
                skip = str(counts["skipped"])
                errc = str(ec)
            else:
                total = ""
                ok = "?"
                bad = str(fc)
                skip = str(counts["skipped"]) if counts["skipped"] else "?"
                errc = str(ec)

        summ_short = (info["summary"] or "—")[:200]
        if len(summ_short) == 200:
            summ_short += "…"
        summary_rows.append(
            [
                _md_cell(job_name),
                _md_cell(total),
                _md_cell(ok),
                _md_cell(bad),
                _md_cell(skip),
                _md_cell(errc),
                _md_cell(summ_short),
            ]
        )

    lines.append("## Summary")
    lines.append("")
    lines.append(
        render_markdown_table(
            ["Job", "Total", "Passed", "Failed", "Skipped", "Errors", "Pytest summary"],
            summary_rows,
        )
    )
    lines.append("")

    for job_name, paths in groups:
        text = read_job_text(paths)
        info = parse_pytest(text)
        lines.append(f"## Job: `{_md_cell(job_name)}`")
        lines.append("")
        rel = ", ".join(f"`{p.name}`" for p in paths)
        lines.append(f"- **Log files:** {rel}")
        if info["summary"]:
            lines.append(f"- **Session line:** {_md_cell(info['summary'])}")
        lines.append("")

        fail_rows: list[list[str]] = []
        for node in info["failed_nodes"]:
            fail_rows.append([_md_cell(node), _md_cell(info["failed_reasons"].get(node, ""))])
        for node in info["error_nodes"]:
            fail_rows.append(
                [_md_cell(node) + " (ERROR)", _md_cell(info["error_reasons"].get(node, ""))]
            )

        if fail_rows:
            lines.append("### Failures & errors")
            lines.append("")
            lines.append(render_markdown_table(["Test node", "Reason"], fail_rows))
            lines.append("")
        else:
            lines.append("*No `FAILED` / `ERROR` nodes in log.*")
            lines.append("")

    print("\n".join(lines), file=out_fp)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Emit Markdown report from logs/nightly_perf_jobs pytest output.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (default: $REPO_ROOT or cwd).",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=None,
        help="Log directory (default: $REPO_ROOT/logs/nightly_perf_jobs).",
    )
    parser.add_argument(
        "--markdown-report",
        type=Path,
        default=None,
        help="Write report to this file (default: stdout).",
    )
    parser.add_argument(
        "--title",
        default="Nightly local test report",
        help="Report H1 title.",
    )
    args = parser.parse_args()

    r_txt = os.environ.get("REPO_ROOT", "").strip()
    if args.repo_root is not None:
        repo = args.repo_root.resolve()
    elif r_txt:
        repo = Path(r_txt).resolve()
    else:
        repo = Path.cwd().resolve()

    log_dir = args.log_dir.resolve() if args.log_dir else default_log_dir(repo)

    out = args.markdown_report
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as fp:
            emit_report(title=args.title, repo_root=repo, log_dir=log_dir, out_fp=fp)
    else:
        emit_report(title=args.title, repo_root=repo, log_dir=log_dir, out_fp=sys.stdout)


if __name__ == "__main__":
    main()
