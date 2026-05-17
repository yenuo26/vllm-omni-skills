#!/usr/bin/env python3
"""Convert compose_full_report.py Markdown output to a standalone HTML document (stdlib only)."""

from __future__ import annotations

import base64
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from report_html_theme import EDITORIAL_THEME_CSS, RELEASE_MARKDOWN_DOC_CSS

# Inserted after ``## 测试结论``; replaced with interactive HTML (release) or static MD table (archive / .md only).
RELEASE_CONCLUSION_PLACEHOLDER = "@@RELEASE_CONCLUSION_WIDGET@@"

RELEASE_CONCLUSION_ITEMS: tuple[str, ...] = (
    "UT覆盖率达到本迭代要求",
    "L2&L3最新一次通过率为100%",
    "需求完成率大于85%",
    "性能劣化小于5%",
    "遗留DI小于30",
    "致命issue遗留个数为0",
    "所有遗留bug均已分配责任人",
)

# 「L2&L3最新一次通过率为100%」：最新已结束 ready + merge 构建均无 failed/broken job
CONCLUSION_L2_L3_ROW_INDEX = 1
# 「致命issue遗留个数为0」：由 compose 检测是否存在 open 且 label 为 ``critical`` 的 issue
CONCLUSION_CRITICAL_ROW_INDEX = 5
# 「所有遗留bug均已分配责任人」：open label:bug 的 assignees
CONCLUSION_ASSIGNEE_ROW_INDEX = 6


def test_conclusion_markdown_for_archive(
    *,
    l2_l3_row_ok: bool | None = None,
    l2_l3_row_detail: str = "",
    critical_row_ok: bool | None = None,
    critical_row_detail: str = "",
    assignee_row_ok: bool | None = None,
    assignee_row_detail: str = "",
) -> str:
    """Static Markdown block (no ``##`` heading): table + **测试结论：** Go / Rejected."""
    lines = [
        "| 检查项 | 检查结果 |",
        "| --- | --- |",
    ]
    verdict_ok = True
    for i, item in enumerate(RELEASE_CONCLUSION_ITEMS):
        safe = item.replace("|", "\\|")
        cell = "通过"
        extra = ""
        if i == CONCLUSION_L2_L3_ROW_INDEX and l2_l3_row_ok is not None:
            cell = "通过" if l2_l3_row_ok else "不通过"
            if not l2_l3_row_ok:
                verdict_ok = False
                if l2_l3_row_detail:
                    extra = f"（{l2_l3_row_detail.replace('|', '/')}）"
        elif i == CONCLUSION_CRITICAL_ROW_INDEX and critical_row_ok is not None:
            cell = "通过" if critical_row_ok else "不通过"
            if not critical_row_ok:
                verdict_ok = False
                if critical_row_detail:
                    extra = f"（{critical_row_detail.replace('|', '/')}）"
        elif i == CONCLUSION_ASSIGNEE_ROW_INDEX and assignee_row_ok is not None:
            cell = "通过" if assignee_row_ok else "不通过"
            if not assignee_row_ok:
                verdict_ok = False
                if assignee_row_detail:
                    extra = f"（{assignee_row_detail.replace('|', '/')}）"
        lines.append(f"| {safe} | {cell}{extra} |")
    vtxt = "Go" if verdict_ok else "Rejected"
    lines.extend(["", f"**测试结论：** {vtxt}", ""])
    return "\n".join(lines)


def release_conclusion_widget_html(
    *,
    l2_l3_row_ok: bool | None = None,
    l2_l3_row_detail: str = "",
    critical_row_ok: bool | None = None,
    critical_row_detail: str = "",
    assignee_row_ok: bool | None = None,
    assignee_row_detail: str = "",
) -> str:
    """Interactive table + verdict (Go / Rejected) for ``.release-doc`` HTML.

    Automatic rows (non-clickable when ``*_row_ok`` is not ``None``): **L2&L3**,
    **致命issue…**, **遗留bug责任人**.
    """
    rows: list[str] = []
    for i, item in enumerate(RELEASE_CONCLUSION_ITEMS):
        auto_ok: bool | None = None
        row_detail = ""
        if i == CONCLUSION_L2_L3_ROW_INDEX:
            auto_ok = l2_l3_row_ok
            row_detail = l2_l3_row_detail
        elif i == CONCLUSION_CRITICAL_ROW_INDEX:
            auto_ok = critical_row_ok
            row_detail = critical_row_detail
        elif i == CONCLUSION_ASSIGNEE_ROW_INDEX:
            auto_ok = assignee_row_ok
            row_detail = assignee_row_detail
        is_auto = auto_ok is not None
        pass_on = bool(auto_ok) if is_auto else True
        pass_cls = "is-on" if pass_on else ""
        fail_cls = "" if pass_on else "is-on"
        pass_pressed = "true" if pass_on else "false"
        fail_pressed = "false" if pass_on else "true"
        auto_cls = " conc-auto" if is_auto else ""
        hint = ""
        if is_auto and row_detail:
            hint = (
                f'<div class="conc-auto-hint">{html.escape(row_detail)}</div>'
            )
        rows.append(
            f'<tr data-conc-row="{i}" data-conc-auto="{"1" if is_auto else "0"}">'
            f'<td>{html.escape(item)}</td>'
            "<td>"
            f'<div class="conc-btns{auto_cls}" role="group" aria-label="检查结果">'
            f'<button type="button" class="conc-btn conc-pass {pass_cls}" data-conc="pass" aria-pressed="{pass_pressed}">通过</button>'
            f'<button type="button" class="conc-btn conc-fail {fail_cls}" data-conc="fail" aria-pressed="{fail_pressed}">不通过</button>'
            f"</div>{hint}</td></tr>"
        )
    rows_s = "\n".join(rows)
    return f"""<div class="release-conclusion-wrap">
<table class="release-conclusion-table">
<thead><tr><th>检查项</th><th>检查结果</th></tr></thead>
<tbody>
{rows_s}
</tbody>
</table>
<p class="release-verdict-line">测试结论： <strong class="release-verdict" id="release-verdict-label">Go</strong></p>
</div>
<script>
(function () {{
  var wrap = document.querySelector('.release-conclusion-wrap');
  if (!wrap) return;
  function allPass() {{
    var rows = wrap.querySelectorAll('tbody tr');
    for (var i = 0; i < rows.length; i++) {{
      var tr = rows[i];
      var on = tr.querySelector('.conc-btn.conc-pass.is-on');
      if (!on) return false;
    }}
    return rows.length > 0;
  }}
  function syncVerdict() {{
    var el = document.getElementById('release-verdict-label');
    if (el) el.textContent = allPass() ? 'Go' : 'Rejected';
  }}
  wrap.addEventListener('click', function (e) {{
    var t = e.target;
    if (!t.classList || !t.classList.contains('conc-btn')) return;
    var tr = t.closest('tr');
    if (!tr) return;
    if (tr.getAttribute('data-conc-auto') === '1') return;
    var pass = t.classList.contains('conc-pass');
    var bp = tr.querySelector('.conc-pass');
    var bf = tr.querySelector('.conc-fail');
    if (!bp || !bf) return;
    if (pass) {{
      bp.classList.add('is-on');
      bf.classList.remove('is-on');
      bp.setAttribute('aria-pressed', 'true');
      bf.setAttribute('aria-pressed', 'false');
    }} else {{
      bf.classList.add('is-on');
      bp.classList.remove('is-on');
      bf.setAttribute('aria-pressed', 'true');
      bp.setAttribute('aria-pressed', 'false');
    }}
    syncVerdict();
  }});
  syncVerdict();
}})();
</script>"""


def apply_release_conclusion_placeholder(
    fragment: str,
    *,
    l2_l3_row_ok: bool | None = None,
    l2_l3_row_detail: str = "",
    critical_row_ok: bool | None = None,
    critical_row_detail: str = "",
    assignee_row_ok: bool | None = None,
    assignee_row_detail: str = "",
) -> str:
    """Replace paragraph-wrapped placeholder with interactive widget."""
    escaped = html.escape(RELEASE_CONCLUSION_PLACEHOLDER, quote=False)
    p_wrap = f"<p>{escaped}</p>"
    widget = release_conclusion_widget_html(
        l2_l3_row_ok=l2_l3_row_ok,
        l2_l3_row_detail=l2_l3_row_detail,
        critical_row_ok=critical_row_ok,
        critical_row_detail=critical_row_detail,
        assignee_row_ok=assignee_row_ok,
        assignee_row_detail=assignee_row_detail,
    )
    if p_wrap in fragment:
        return fragment.replace(p_wrap, widget, 1)
    if RELEASE_CONCLUSION_PLACEHOLDER in fragment:
        return fragment.replace(RELEASE_CONCLUSION_PLACEHOLDER, widget, 1)
    return fragment


def materialize_release_conclusion_in_markdown(
    md: str,
    *,
    l2_l3_row_ok: bool | None = None,
    l2_l3_row_detail: str = "",
    critical_row_ok: bool | None = None,
    critical_row_detail: str = "",
    assignee_row_ok: bool | None = None,
    assignee_row_detail: str = "",
) -> str:
    """Replace placeholder with static Markdown (archived .md or ``--format markdown`` output)."""
    if RELEASE_CONCLUSION_PLACEHOLDER not in md:
        return md
    block = test_conclusion_markdown_for_archive(
        l2_l3_row_ok=l2_l3_row_ok,
        l2_l3_row_detail=l2_l3_row_detail,
        critical_row_ok=critical_row_ok,
        critical_row_detail=critical_row_detail,
        assignee_row_ok=assignee_row_ok,
        assignee_row_detail=assignee_row_detail,
    )
    return md.replace(RELEASE_CONCLUSION_PLACEHOLDER, block, 1)


def _italic_in_plain(s: str) -> str:
    """Apply *em* to raw ``s``; escape remaining text."""
    parts = re.split(r"(\*[^*]+\*)", s)
    out: list[str] = []
    for p in parts:
        if len(p) >= 2 and p[0] == "*" and p[-1] == "*" and not p.startswith("**"):
            inner = p[1:-1]
            out.append("<em>" + html.escape(inner) + "</em>")
        else:
            out.append(html.escape(p))
    return "".join(out)


def _bold_italic_plain(s: str) -> str:
    parts = re.split(r"(\*\*[^*]+\*\*)", s)
    res: list[str] = []
    for p in parts:
        if p.startswith("**") and p.endswith("**") and len(p) >= 4:
            res.append("<strong>" + _italic_in_plain(p[2:-2]) + "</strong>")
        else:
            res.append(_italic_in_plain(p))
    return "".join(res)


def _inline_text_with_links(s: str) -> str:
    out: list[str] = []
    pos = 0
    for m in re.finditer(r"\[([^\]]*)\]\(([^)]+)\)", s):
        out.append(_bold_italic_plain(s[pos : m.start()]))
        url = html.escape(m.group(2), quote=True)
        inner = _bold_italic_plain(m.group(1))
        out.append(f'<a href="{url}">{inner}</a>')
        pos = m.end()
    out.append(_bold_italic_plain(s[pos:]))
    return "".join(out)


def inline_md_to_html(s: str) -> str:
    if not s:
        return ""
    chunks: list[tuple[str, str]] = []
    last = 0
    for m in re.finditer(r"`([^`]+)`", s):
        chunks.append(("t", s[last : m.start()]))
        chunks.append(("c", m.group(1)))
        last = m.end()
    chunks.append(("t", s[last:]))
    out: list[str] = []
    for kind, content in chunks:
        if kind == "c":
            out.append("<code>" + html.escape(content) + "</code>")
        else:
            out.append(_inline_text_with_links(content))
    return "".join(out)


def _parse_table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    if not cells:
        return False
    return all(
        bool(re.match(r"^:?-{3,}:?$", (c or "").strip())) for c in cells
    )


def _render_md_table(tbl_lines: list[str]) -> str:
    rows = [_parse_table_row(L) for L in tbl_lines]
    if not rows:
        return ""
    i = 0
    header = rows[i]
    i += 1
    if i < len(rows) and _is_separator_row(rows[i]):
        i += 1
    body_rows = rows[i:]
    parts = ["<table>", "<thead><tr>"]
    for h in header:
        parts.append(f"<th>{inline_md_to_html(h)}</th>")
    parts.extend(["</tr></thead>", "<tbody>"])
    for r in body_rows:
        parts.append("<tr>")
        # pad short rows
        while len(r) < len(header):
            r.append("")
        for c in r[: len(header)]:
            parts.append(f"<td>{inline_md_to_html(c)}</td>")
        parts.append("</tr>")
    parts.extend(["</tbody>", "</table>"])
    inner = "\n".join(parts)
    return f'<div class="table-scroll">\n{inner}\n</div>'


def convert_markdown_to_html_body(md: str) -> str:
    lines = md.splitlines()
    html_parts: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("|"):
            tbl_lines: list[str] = []
            while i < n and lines[i].strip().startswith("|"):
                tbl_lines.append(lines[i])
                i += 1
            html_parts.append(_render_md_table(tbl_lines))
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            level = min(len(m.group(1)), 6)
            content = m.group(2)
            tag = f"h{level}"
            html_parts.append(f"<{tag}>{inline_md_to_html(content)}</{tag}>")
            i += 1
            continue
        if re.match(r"^[-*]\s+", stripped):
            items: list[str] = []
            while i < n:
                s = lines[i].strip()
                if re.match(r"^[-*]\s+", s):
                    items.append(re.sub(r"^[-*]\s+", "", s))
                    i += 1
                elif not s:
                    i += 1
                    break
                else:
                    break
            lis = "\n".join(f"<li>{inline_md_to_html(it)}</li>" for it in items)
            html_parts.append(f"<ul>\n{lis}\n</ul>")
            continue
        para: list[str] = []
        while i < n:
            s = lines[i]
            st = s.strip()
            if not st:
                break
            if st.startswith("|") or re.match(r"^#{1,6}\s", st) or re.match(
                r"^[-*]\s+", st
            ):
                break
            para.append(s)
            i += 1
        text = " ".join(p.strip() for p in para)
        if text:
            html_parts.append(f"<p>{inline_md_to_html(text)}</p>")
    return "\n".join(html_parts)


def _markdown_skip_document_h1(md: str) -> str:
    """Remove the first ``# document title`` so it is not repeated below the top bar."""
    lines = md.splitlines()
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines):
        return md
    head = lines[i]
    if not re.match(r"^#\s+\S", head) or head.startswith("##"):
        return md
    i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    return "\n".join(lines[i:])


def _release_brand_clipboard_svg() -> str:
    return (
        '<svg class="ico brand-ico" width="30" height="30" viewBox="0 0 24 24" '
        'aria-hidden="true" focusable="false" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>'
        '<rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>'
        "</svg>"
    )


def _default_archive_filename(title: str, generated_utc: str) -> str:
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", generated_utc.strip())
    date_part = m.group(1) if m else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    base = "vllm-omni-test-report"
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", title).strip("-")[:72]
    if slug:
        return f"{slug}-{date_part}.md"
    return f"{base}-{date_part}.md"


def wrap_html_document(
    *,
    title: str,
    body_inner: str,
    generated_utc: str | None = None,
    tagline: str = "Release · CI test report",
    archive_markdown: str | None = None,
    archive_download_name: str | None = None,
) -> str:
    t = html.escape(title)
    when = generated_utc or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    meta = f'<p class="meta generated-meta">Generated: {html.escape(when)}</p>'
    brand = _release_brand_clipboard_svg()
    tl = html.escape(tagline)
    css = EDITORIAL_THEME_CSS + "\n" + RELEASE_MARKDOWN_DOC_CSS
    dl_name = archive_download_name or _default_archive_filename(
        title, when
    )
    dl_name_esc = html.escape(dl_name, quote=True)
    archive_top = ""
    archive_scripts = ""
    if archive_markdown is not None:
        b64 = base64.b64encode(archive_markdown.encode("utf-8")).decode("ascii")
        b64_json = json.dumps(b64)
        archive_top = (
            '<div class="top-bar-actions">'
            '<button type="button" class="btn-release-archive" '
            'id="release-archive-md-btn" '
            f'data-download-name="{dl_name_esc}" '
            'title="下载与当前报告内容一致的 Markdown 文件（供归档或 patch_report_*.py）">'
            "归档 Markdown</button>"
            "</div>"
        )
        archive_scripts = (
            f'<script type="application/json" id="release-archive-md-b64">{b64_json}</script>\n'
            """<script>
(function () {
  var btn = document.getElementById("release-archive-md-btn");
  var el = document.getElementById("release-archive-md-b64");
  if (!btn || !el) return;
  btn.addEventListener("click", function () {
    try {
      var b64 = JSON.parse(el.textContent || '""');
      var bin = atob(b64);
      var bytes = new Uint8Array(bin.length);
      for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      var text = new TextDecoder("utf-8").decode(bytes);
      var blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
      var url = URL.createObjectURL(blob);
      var a = document.createElement("a");
      a.href = url;
      a.download = btn.getAttribute("data-download-name") || "vllm-omni-test-report.md";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      alert("归档失败: " + e);
    }
  });
})();
</script>"""
        )
    top_bar = (
        '<div class="top-bar"><div class="shell top-bar-inner">'
        '<div class="brand">'
        f'<div class="brand-mark">{brand}</div>'
        '<div class="brand-copy">'
        f"<h1>{t}</h1>"
        f'<p class="tagline">{tl}</p>'
        "</div></div>"
        f"{archive_top}"
        "</div></div>"
    )
    shell = (
        '<div class="shell">'
        '<div class="panel release-doc">'
        f"{meta}\n{body_inner}"
        "</div></div>"
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<style>
{css}
</style>
</head>
<body>
{top_bar}
{shell}
{archive_scripts}
</body>
</html>
"""


def convert_release_report_markdown(
    md: str,
    *,
    archive_download_name: str | None = None,
    l2_l3_row_ok: bool | None = None,
    l2_l3_row_detail: str = "",
    critical_row_ok: bool | None = None,
    critical_row_detail: str = "",
    assignee_row_ok: bool | None = None,
    assignee_row_detail: str = "",
) -> str:
    """Full HTML document from a release report Markdown string.

    自动结论行需传入对应 ``*_row_ok``；未传入时该行在归档表中默认「通过」。
    """
    title = "vLLM-Omni Test Report"
    for line in md.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    when = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    md_body = _markdown_skip_document_h1(md)
    body = convert_markdown_to_html_body(md_body)
    body = apply_release_conclusion_placeholder(
        body,
        l2_l3_row_ok=l2_l3_row_ok,
        l2_l3_row_detail=l2_l3_row_detail,
        critical_row_ok=critical_row_ok,
        critical_row_detail=critical_row_detail,
        assignee_row_ok=assignee_row_ok,
        assignee_row_detail=assignee_row_detail,
    )
    archive_markdown = materialize_release_conclusion_in_markdown(
        md,
        l2_l3_row_ok=l2_l3_row_ok,
        l2_l3_row_detail=l2_l3_row_detail,
        critical_row_ok=critical_row_ok,
        critical_row_detail=critical_row_detail,
        assignee_row_ok=assignee_row_ok,
        assignee_row_detail=assignee_row_detail,
    )
    return wrap_html_document(
        title=title,
        body_inner=body,
        generated_utc=when,
        archive_markdown=archive_markdown,
        archive_download_name=archive_download_name,
    )
