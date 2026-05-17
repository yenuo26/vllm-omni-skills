#!/usr/bin/env python3
"""Shared editorial HTML theme (nightly + release reports)."""

from __future__ import annotations

# Full theme: CSS variables, top-bar, panels, tables, nightly-only components.
EDITORIAL_THEME_CSS = """
:root {
  /* Dashboard palette (aligned with omni docs / slate home — cool gray, blue accent) */
  --dashboard-bg: #f5f8fb;
  --dashboard-panel-bg: #ffffff;
  --dashboard-panel-strong: #f1f5f9;
  --dashboard-border: #d9e2ec;
  --dashboard-border-strong: #d6dde6;
  --dashboard-text: #26323f;
  --dashboard-muted: #607080;
  --dashboard-soft-text: #52606d;
  --dashboard-shadow: 0 18px 38px rgba(15, 23, 42, 0.08);
  --dashboard-badge-bg: #edf3f8;
  --dashboard-badge-text: #435466;
  --dashboard-chart-text: #5b6775;
  --dashboard-chart-grid: rgba(148, 163, 184, 0.2);
  --omni-baseline-line: #64748b;
  --omni-baseline-label-bg: rgba(241, 245, 249, 0.96);
  --omni-baseline-label-fg: #0f172a;
  --omni-baseline-label-border: rgba(100, 116, 139, 0.45);
  --dashboard-tooltip-bg: rgba(15, 23, 42, 0.92);
  --dashboard-tooltip-border: rgba(148, 163, 184, 0.28);
  --dashboard-tooltip-text: #f8fafc;
  --dashboard-healthy: #1f9d63;
  --dashboard-alert: #d14343;
  --dashboard-healthy-bg: rgba(31, 157, 99, 0.1);
  --dashboard-alert-bg: rgba(209, 67, 67, 0.11);
  --dashboard-warning: #d97706;
  --dashboard-warning-bg: rgba(217, 119, 6, 0.12);
  --dashboard-violet: #4f46e5;
  --dashboard-violet-bg: rgba(79, 70, 229, 0.1);
  /* Internal aliases (report markup) */
  --bg: var(--dashboard-bg);
  --surface: var(--dashboard-panel-bg);
  --surface-muted: #edf3f8;
  --text: var(--dashboard-text);
  --muted: var(--dashboard-muted);
  --border: var(--dashboard-border);
  --shadow: var(--dashboard-shadow);
  --accent: #3b82f6;
  --accent-hover: #2563eb;
  --accent-soft: rgba(59, 130, 246, 0.22);
  --accent-tint: rgba(59, 130, 246, 0.08);
  --ci: #2563eb;
  --ci-soft: rgba(59, 130, 246, 0.16);
  --danger: var(--dashboard-alert);
  --danger-strong: #b91c1c;
  --danger-bg: rgba(209, 67, 67, 0.08);
  --danger-edge: var(--dashboard-alert);
  --ok: var(--dashboard-healthy);
  --ok-bg: var(--dashboard-healthy-bg);
  --ok-edge: var(--dashboard-healthy);
  --fail-bg: var(--dashboard-alert-bg);
  --fail-edge: var(--dashboard-alert);
  --unknown-bg: rgba(148, 163, 184, 0.08);
  --unknown-edge: #64748b;
  --code-bg-top: #334155;
  --code-bg-bottom: #1e293b;
  --code-fg: #e2e8f0;
  --radius: 12px;
  --radius-sm: 8px;
  --shadow-bar: none;
}
@media (prefers-color-scheme: dark) {
  :root {
    --dashboard-bg: #111827;
    --dashboard-panel-bg: #162130;
    --dashboard-panel-strong: #131d2b;
    --dashboard-border: rgba(148, 163, 184, 0.18);
    --dashboard-border-strong: rgba(148, 163, 184, 0.22);
    --dashboard-text: #edf3fb;
    --dashboard-muted: #b6c4d5;
    --dashboard-soft-text: #c6d3e1;
    --dashboard-shadow: 0 20px 40px rgba(2, 6, 23, 0.35);
    --dashboard-badge-bg: rgba(148, 163, 184, 0.12);
    --dashboard-badge-text: #d5dfeb;
    --dashboard-chart-text: #c8d4e3;
    --dashboard-chart-grid: rgba(148, 163, 184, 0.16);
    --omni-baseline-line: #94a3b8;
    --omni-baseline-label-bg: rgba(30, 41, 55, 0.94);
    --omni-baseline-label-fg: #f1f5f9;
    --omni-baseline-label-border: rgba(148, 163, 184, 0.4);
    --dashboard-tooltip-bg: rgba(15, 23, 42, 0.96);
    --dashboard-tooltip-border: rgba(148, 163, 184, 0.24);
    --dashboard-tooltip-text: #f8fafc;
    --dashboard-healthy-bg: rgba(31, 157, 99, 0.16);
    --dashboard-alert-bg: rgba(209, 67, 67, 0.18);
    --dashboard-warning: #fbbf24;
    --dashboard-warning-bg: rgba(251, 191, 36, 0.14);
    --dashboard-violet: #818cf8;
    --dashboard-violet-bg: rgba(129, 140, 248, 0.14);
    --surface-muted: rgba(148, 163, 184, 0.1);
    --accent: #60a5fa;
    --accent-hover: #3b82f6;
    --accent-soft: rgba(96, 165, 250, 0.28);
    --accent-tint: rgba(96, 165, 250, 0.12);
    --ci: #60a5fa;
    --ci-soft: rgba(96, 165, 250, 0.2);
    --danger-strong: #fecaca;
    --danger-bg: rgba(209, 67, 67, 0.14);
    --unknown-bg: rgba(148, 163, 184, 0.08);
    --unknown-edge: #94a3b8;
  }
}
* { box-sizing: border-box; }
body {
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  margin: 0;
  padding: 0;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  font-size: 15px;
}
.top-bar {
  background: var(--dashboard-panel-bg);
  color: var(--dashboard-text);
  padding: 0;
  box-shadow: 0 1px 0 rgba(148, 163, 184, 0.18);
  border-bottom: 3px solid var(--accent);
}
.top-bar-inner {
  padding: 1.4rem 1.25rem 1.55rem;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}
.brand {
  display: flex;
  align-items: center;
  gap: 1.1rem;
}
.brand-mark {
  width: 3.2rem;
  height: 3.2rem;
  border-radius: var(--radius-sm);
  background: var(--dashboard-badge-bg);
  border: 1px solid var(--dashboard-border);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
}
.brand-mark .ico { stroke: var(--accent); }
.brand-copy h1 {
  margin: 0;
  font-size: 1.65rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.15;
  color: var(--dashboard-text);
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
.tagline {
  margin: 0.35rem 0 0;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
.top-bar .tagline {
  color: var(--dashboard-muted);
}
.shell {
  max-width: 1280px;
  margin: 0 auto;
  padding: 1.5rem 1.25rem 3rem;
}
.panel {
  background: var(--dashboard-panel-bg);
  border-radius: var(--radius);
  border: 1px solid var(--dashboard-border);
  box-shadow: var(--dashboard-shadow);
  padding: 1.15rem 1.3rem;
  margin-bottom: 1.35rem;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.panel:hover {
  box-shadow: 0 16px 28px rgba(15, 23, 42, 0.1);
  border-color: rgba(59, 130, 246, 0.28);
}
.panel h2 {
  margin: 0 0 1rem;
  font-size: 1.12rem;
  font-weight: 800;
  color: var(--dashboard-text);
  letter-spacing: -0.02em;
  border-bottom: 2px solid var(--dashboard-border);
  padding-bottom: 0.55rem;
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
.panel-bk h2 {
  border-bottom-color: var(--ci-soft);
}
.heading-row {
  display: inline-flex;
  align-items: flex-start;
  gap: 0.65rem;
}
.heading-ico {
  display: flex;
  margin-top: 0.12rem;
  color: var(--accent);
}
.panel-bk .heading-ico {
  color: var(--ci);
}
.heading-text {
  display: flex;
  flex-direction: column;
  gap: 0.12rem;
  min-width: 0;
}
.heading-sub {
  font-size: 0.78em;
  font-weight: 500;
  color: var(--muted);
}
h3.panel-sub {
  margin: 1.2rem 0 0.65rem;
  font-size: 1.04rem;
  color: var(--dashboard-soft-text);
  font-weight: 700;
}
h3.panel-sub:first-child {
  margin-top: 0;
}
h3.panel-sub .heading-ico {
  color: var(--dashboard-muted);
}
h3.section-failures {
  margin: 0 0 0.85rem;
  font-size: 1.02rem;
  font-weight: 700;
  color: var(--danger-strong);
}
h3.section-failures .heading-ico {
  color: var(--danger);
}
section.job-fail-bk h3.section-failures .heading-ico {
  color: var(--ci);
}
.panel-fail-analysis {
  border-top: 3px solid var(--dashboard-warning);
  background: linear-gradient(180deg, color-mix(in srgb, var(--dashboard-warning-bg) 65%, var(--dashboard-panel-bg)) 0%, var(--dashboard-panel-bg) 42%);
}
.panel-fail-analysis > h2 {
  border-bottom-color: color-mix(in srgb, var(--dashboard-warning) 35%, transparent);
}
.panel-fail-analysis .heading-ico {
  color: var(--dashboard-warning);
}
.panel-perf-manual {
  border-top: 3px solid var(--dashboard-violet);
  background: linear-gradient(180deg, color-mix(in srgb, var(--dashboard-violet-bg) 55%, var(--dashboard-panel-bg)) 0%, var(--dashboard-panel-bg) 45%);
}
.panel-perf-manual > h2 {
  border-bottom-color: color-mix(in srgb, var(--dashboard-violet) 30%, transparent);
}
.panel-perf-manual .heading-ico {
  color: var(--dashboard-violet);
}
h3.perf-sheet-title {
  margin: 1.25rem 0 0.55rem;
  font-size: 1rem;
  font-weight: 700;
  color: var(--dashboard-violet);
}
h3.perf-sheet-title:first-of-type {
  margin-top: 0.35rem;
}
.perf-truncate-hint {
  margin: 0 0 0.5rem !important;
}
table.perf-manual {
  font-size: 0.86rem;
}
table.perf-manual th {
  background: linear-gradient(180deg, color-mix(in srgb, var(--dashboard-violet-bg) 85%, var(--dashboard-panel-bg)) 0%, var(--dashboard-panel-strong));
  color: var(--dashboard-text);
}
table.perf-manual td {
  background: color-mix(in srgb, var(--dashboard-panel-bg) 96%, var(--dashboard-badge-bg));
}
.perf-delta {
  font-size: 0.78em;
  font-weight: 750;
  margin-left: 0.35rem;
  white-space: nowrap;
}
.perf-delta--up {
  color: var(--dashboard-warning);
}
.perf-delta--down {
  color: var(--dashboard-healthy);
}
details.job-fail-details {
  margin-bottom: 1.25rem;
  border-radius: var(--radius);
  overflow: hidden;
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
  border-left: 4px solid var(--danger-edge);
  background: var(--surface);
}
details.job-fail-details:last-child {
  margin-bottom: 0;
}
summary.job-fail-details-summary {
  list-style: none;
  cursor: pointer;
  background: var(--danger-bg);
  padding: 1.05rem 1.1rem 1.05rem 2.65rem;
  border-bottom: 1px solid color-mix(in srgb, var(--dashboard-warning) 38%, transparent);
  position: relative;
}
summary.job-fail-details-summary::-webkit-details-marker {
  display: none;
}
summary.job-fail-details-summary::before {
  content: "▸";
  position: absolute;
  left: 0.95rem;
  top: 1.2rem;
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--danger-strong);
  line-height: 1;
}
details.job-fail-details[open] > summary.job-fail-details-summary::before {
  content: "▾";
}
summary.job-fail-details-summary h2 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 750;
  color: var(--danger-strong);
}
summary.job-fail-details-summary .heading-ico {
  color: var(--danger-strong);
}
summary.job-fail-details-summary .meta {
  margin: 0.5rem 0 0;
}
.job-fail-details-body {
  padding: 1.1rem 1.35rem 1.35rem;
  background: linear-gradient(180deg, color-mix(in srgb, var(--dashboard-alert-bg) 40%, var(--dashboard-panel-bg)) 0%, var(--dashboard-panel-bg) 48%);
}
.full-log-wrap {
  margin: 0.55rem 0 0;
  padding-top: 0.4rem;
  border-top: 1px dashed color-mix(in srgb, var(--dashboard-warning) 42%, transparent);
}
.btn-view-full-log {
  display: inline-flex;
  align-items: center;
  padding: 0.42rem 0.88rem;
  border-radius: 9px;
  border: 1px solid color-mix(in srgb, var(--dashboard-warning) 45%, var(--dashboard-border));
  background: linear-gradient(180deg, var(--dashboard-panel-bg) 0%, color-mix(in srgb, var(--dashboard-warning-bg) 55%, var(--dashboard-panel-bg)) 100%);
  color: var(--danger-strong);
  font-size: 0.86rem;
  font-weight: 650;
  cursor: pointer;
  box-shadow: 0 1px 2px color-mix(in srgb, var(--dashboard-warning) 12%, transparent);
}
.btn-view-full-log:hover {
  border-color: var(--dashboard-warning);
  background: var(--dashboard-panel-bg);
}
.full-log-panel {
  margin-top: 0.65rem;
}
pre.log-full {
  margin: 0;
  padding: 0.85rem 1rem;
  background: linear-gradient(180deg, var(--code-bg-top) 0%, var(--code-bg-bottom) 100%);
  color: var(--code-fg);
  border-radius: var(--radius-sm);
  border: 1px solid color-mix(in srgb, var(--dashboard-muted) 38%, transparent);
  font-size: 0.78rem;
  line-height: 1.48;
  max-height: min(75vh, 42rem);
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
ul.full-log-paths {
  margin: 0.35rem 0 0;
  padding-left: 1.25rem;
  font-size: 0.88rem;
  color: var(--text);
}
.full-log-oversize {
  margin: 0;
}
summary.job-fail-details-summary-bk {
  background: linear-gradient(180deg, color-mix(in srgb, var(--ci-soft) 65%, var(--dashboard-panel-bg)) 0%, var(--dashboard-panel-strong));
  border-bottom-color: color-mix(in srgb, var(--ci) 42%, transparent);
}
summary.job-fail-details-summary-bk::before {
  color: var(--ci);
}
details.job-fail-details-bk {
  border-left-color: var(--ci);
}
summary.job-fail-details-summary-bk h2 {
  color: var(--dashboard-chart-text);
}
summary.job-fail-details-summary-bk .heading-ico {
  color: var(--ci);
}
.meta {
  color: var(--muted);
  font-size: 0.9rem;
  margin: 0.4rem 0;
}
.meta strong {
  color: var(--dashboard-badge-text);
  font-weight: 650;
}
.meta a {
  color: var(--accent);
  font-weight: 600;
  text-decoration: none;
  border-bottom: 1px solid var(--accent-soft);
}
.meta a:hover {
  color: var(--accent-hover);
  border-bottom-color: var(--accent);
}
.hint {
  color: var(--muted);
  font-size: 0.88rem;
  margin: 0.55rem 0 0;
  display: flex;
  align-items: flex-start;
  gap: 0.45rem;
}
.hint::before {
  content: "→";
  color: var(--accent);
  font-weight: 800;
  flex-shrink: 0;
  margin-top: 0.08rem;
}
p.summary-legend {
  margin: 0.35rem 0 0;
  font-size: 0.84rem;
}
.summary-legend strong.summary-legend--ok { color: var(--dashboard-healthy); }
.summary-legend strong.summary-legend--fail { color: var(--dashboard-alert); }
.summary-legend strong.summary-legend--unk { color: var(--omni-baseline-line); }
.table-scroll {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  border-radius: var(--radius-sm);
  margin: 0.65rem 0 0;
  border: 1px solid var(--border);
  background: var(--surface-muted);
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--dashboard-panel-bg) 65%, transparent);
}
.table-scroll > table {
  width: 100%;
  min-width: 620px;
}
table.summary {
  border-collapse: collapse;
  font-size: 0.92rem;
}
table.summary th, table.summary td {
  border: 1px solid var(--border);
  padding: 0.65rem 0.8rem;
  text-align: left;
  vertical-align: top;
}
table.summary th {
  background: var(--dashboard-panel-strong);
  font-weight: 650;
  color: var(--dashboard-chart-text);
  white-space: nowrap;
}
table.summary tbody tr.summary-row--ok td {
  background: color-mix(in srgb, var(--dashboard-healthy-bg) 92%, var(--dashboard-panel-bg));
}
table.summary tbody tr.summary-row--ok td:first-child {
  border-left: 4px solid var(--ok-edge);
  padding-left: calc(0.8rem - 3px);
  font-weight: 650;
  color: var(--dashboard-healthy);
}
table.summary tbody tr.summary-row--fail td {
  background: color-mix(in srgb, var(--dashboard-alert-bg) 88%, var(--dashboard-panel-bg));
}
table.summary tbody tr.summary-row--fail td:first-child {
  border-left: 4px solid var(--fail-edge);
  padding-left: calc(0.8rem - 3px);
  font-weight: 650;
  color: var(--danger-strong);
}
table.summary tbody tr.summary-row--unknown td {
  background: var(--unknown-bg);
}
table.summary tbody tr.summary-row--unknown td:first-child {
  border-left: 4px solid var(--unknown-edge);
  padding-left: calc(0.8rem - 3px);
  color: var(--dashboard-chart-text);
}
table.summary tbody tr.summary-row--ok:hover td {
  background: color-mix(in srgb, var(--dashboard-healthy-bg) 98%, var(--dashboard-panel-bg));
}
table.summary tbody tr.summary-row--fail:hover td {
  background: color-mix(in srgb, var(--dashboard-alert-bg) 95%, var(--dashboard-panel-bg));
}
table.summary tbody tr.summary-row--unknown:hover td {
  background: var(--dashboard-badge-bg);
}
section.job-fail {
  background: var(--surface);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
  margin-bottom: 1.5rem;
  overflow: hidden;
  border-left: 4px solid var(--danger-edge);
}
section.job-fail header {
  background: var(--danger-bg);
  padding: 1.05rem 1.35rem;
  border-bottom: 1px solid color-mix(in srgb, var(--dashboard-warning) 38%, transparent);
}
section.job-fail header .heading-ico {
  color: var(--danger-strong);
}
section.job-fail h2 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 750;
  color: var(--danger-strong);
}
section.job-fail .body {
  padding: 1.1rem 1.35rem 1.35rem;
  background: linear-gradient(180deg, color-mix(in srgb, var(--dashboard-alert-bg) 35%, var(--dashboard-panel-bg)) 0%, var(--dashboard-panel-bg) 48%);
}
table.fail-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}
table.fail-table th, table.fail-table td {
  border: 1px solid var(--border);
  padding: 0.72rem 0.8rem;
  vertical-align: top;
}
table.fail-table th {
  background: var(--dashboard-panel-strong);
  font-weight: 650;
  text-align: left;
  color: var(--dashboard-text);
}
.th-lbl {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
}
.th-ico {
  flex-shrink: 0;
  opacity: 0.88;
  color: var(--dashboard-chart-text);
}
table.fail-table tr.row-error {
  background: linear-gradient(90deg, color-mix(in srgb, var(--dashboard-warning-bg) 70%, var(--dashboard-panel-bg)) 0%, var(--dashboard-panel-bg) 100%);
}
td.mono {
  font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
  font-size: 0.84rem;
  word-break: break-all;
}
td.reason {
  color: var(--dashboard-text);
}
td.analysis {
  color: var(--dashboard-healthy);
  background: linear-gradient(180deg, color-mix(in srgb, var(--dashboard-healthy-bg) 55%, var(--dashboard-panel-bg)) 0%, color-mix(in srgb, var(--dashboard-healthy-bg) 88%, var(--dashboard-panel-bg)) 100%);
  font-size: 0.86rem;
  border-left: 3px solid var(--dashboard-healthy) !important;
}
td.excerpt-cell {
  padding: 0.5rem !important;
  background: var(--surface-muted);
}
pre.log-excerpt {
  margin: 0;
  padding: 0.85rem 1rem;
  background: linear-gradient(180deg, var(--code-bg-top) 0%, var(--code-bg-bottom) 100%);
  color: var(--code-fg);
  border-radius: var(--radius-sm);
  border: 1px solid color-mix(in srgb, var(--dashboard-muted) 38%, transparent);
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--dashboard-panel-bg) 18%, transparent);
  font-size: 0.78rem;
  line-height: 1.48;
  max-height: 28rem;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
.note {
  color: var(--muted);
  font-size: 0.9rem;
  margin-top: 0.35rem;
}
.panel-bk {
  border-top: 4px solid var(--ci);
  background: linear-gradient(180deg, var(--dashboard-panel-bg) 0%, color-mix(in srgb, var(--ci-soft) 35%, var(--dashboard-panel-bg)) 100%);
}
section.job-fail-bk {
  border-left-color: var(--ci);
}
section.job-fail-bk header {
  background: linear-gradient(180deg, color-mix(in srgb, var(--ci-soft) 55%, var(--dashboard-panel-bg)) 0%, var(--dashboard-panel-strong));
  border-bottom: 1px solid color-mix(in srgb, var(--ci) 38%, transparent);
}
section.job-fail-bk header .heading-ico {
  color: var(--ci);
}
section.job-fail-bk h2 {
  color: var(--dashboard-chart-text);
  font-weight: 750;
}
.issue-action-cell {
  width: 7.5rem;
  text-align: center;
  vertical-align: middle !important;
  background: var(--surface-muted);
}
.btn-github-issue {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  padding: 0.4rem 0.65rem;
  border-radius: 9px;
  border: 1px solid var(--border);
  background: var(--dashboard-panel-strong);
  color: var(--dashboard-text);
  font-size: 0.82rem;
  font-weight: 650;
  cursor: pointer;
  box-shadow: 0 1px 2px color-mix(in srgb, var(--dashboard-shadow) 25%, transparent);
  transition: background 0.15s ease, border-color 0.15s ease, transform 0.1s ease;
}
.btn-github-issue:hover {
  background: linear-gradient(180deg, color-mix(in srgb, var(--accent-tint) 90%, var(--dashboard-panel-bg)) 0%, var(--dashboard-panel-strong));
  border-color: color-mix(in srgb, var(--accent) 35%, var(--dashboard-border));
  color: var(--accent-hover);
}
.btn-github-issue:active { transform: scale(0.98); }
.btn-issue-ico { stroke: var(--accent); }
.btn-issue-text { white-space: nowrap; }
.gh-modal[hidden] { display: none !important; }
.gh-modal:not([hidden]) {
  position: fixed;
  inset: 0;
  z-index: 99990;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}
.gh-modal-backdrop {
  position: absolute;
  inset: 0;
  background: color-mix(in srgb, var(--dashboard-tooltip-bg) 55%, transparent);
  backdrop-filter: blur(3px);
}
.gh-modal-panel {
  position: relative;
  z-index: 1;
  max-width: 720px;
  width: 100%;
  max-height: min(92vh, 920px);
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  box-shadow: var(--dashboard-shadow);
  overflow: hidden;
}
.gh-modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.15rem;
  background: var(--dashboard-panel-strong);
  border-bottom: 1px solid var(--border);
}
.gh-modal-head h2 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 750;
  color: var(--dashboard-text);
}
.gh-modal-x {
  border: none;
  background: transparent;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  color: var(--muted);
  padding: 0 0.25rem;
}
.gh-modal-x:hover { color: var(--danger-strong); }
.gh-modal-hint {
  margin: 0;
  padding: 0.85rem 1.15rem 0;
  font-size: 0.88rem;
  color: var(--muted);
  line-height: 1.55;
}
.gh-modal-hint a { color: var(--accent); font-weight: 600; }
.gh-issue-textarea {
  margin: 0.75rem 1.15rem;
  flex: 1;
  min-height: 200px;
  font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
  font-size: 0.8rem;
  line-height: 1.45;
  padding: 0.75rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  resize: vertical;
  color: var(--dashboard-text);
  background: color-mix(in srgb, var(--dashboard-badge-bg) 40%, var(--dashboard-panel-bg));
}
.gh-modal-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  padding: 0.85rem 1.15rem 1.1rem;
  border-top: 1px solid var(--border);
  background: var(--surface-muted);
}
.btn-gh-copy {
  padding: 0.5rem 1rem;
  border-radius: 9px;
  border: 1px solid var(--border);
  background: var(--dashboard-panel-bg);
  font-weight: 650;
  cursor: pointer;
  color: var(--dashboard-soft-text);
}
.btn-gh-copy:hover { border-color: var(--dashboard-border-strong); }
.btn-gh-open {
  display: inline-flex;
  align-items: center;
  padding: 0.5rem 1.1rem;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: var(--dashboard-tooltip-text) !important;
  font-weight: 700;
  text-decoration: none !important;
  border: 1px solid var(--accent-hover);
  box-shadow: none;
}
.btn-gh-open:hover { background: var(--accent-hover); filter: none; }
/* Nightly report: Buildkite Test / Local Test outer cards + collapsible subcards */
.nightly-root.panel {
  margin-bottom: 1.35rem;
}
.nightly-root--buildkite {
  border-top: 4px solid var(--ci);
  background: linear-gradient(180deg, var(--dashboard-panel-bg) 0%, color-mix(in srgb, var(--ci-soft) 28%, var(--dashboard-panel-bg)) 100%);
}
.nightly-root--local {
  border-top: 4px solid var(--accent);
  background: linear-gradient(180deg, var(--dashboard-panel-bg) 0%, color-mix(in srgb, var(--accent-tint) 70%, var(--dashboard-panel-bg)) 100%);
}
details.report-subcard {
  margin-bottom: 0.9rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--dashboard-border);
  background: var(--dashboard-panel-bg);
  box-shadow: var(--dashboard-shadow);
  overflow: hidden;
}
details.report-subcard:last-child {
  margin-bottom: 0;
}
summary.report-subcard-summary {
  list-style: none;
  cursor: pointer;
  padding: 0.78rem 1rem 0.78rem 2.45rem;
  position: relative;
  font-weight: 780;
  font-size: 1.02rem;
  color: var(--dashboard-text);
  background: linear-gradient(180deg, var(--dashboard-panel-strong) 0%, var(--dashboard-panel-bg) 100%);
  border-bottom: 1px solid var(--dashboard-border);
}
.report-subcard-summary-inner {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  min-width: 0;
}
.report-subcard-summary-inner .report-subcard-ico {
  flex-shrink: 0;
  opacity: 0.92;
}
.report-subcard-title {
  font-weight: inherit;
}
.report-subcard-summary .report-subcard-ico {
  color: var(--accent);
}
.report-subcard--bk .report-subcard-summary .report-subcard-ico {
  color: var(--ci);
}
.report-subcard--bk-fail .report-subcard-summary .report-subcard-ico {
  color: var(--dashboard-warning);
}
.report-subcard--perf .report-subcard-summary .report-subcard-ico {
  color: var(--dashboard-violet);
}
.report-subcard--local-fail .report-subcard-summary .report-subcard-ico {
  color: var(--danger-strong);
}
summary.report-subcard-summary::-webkit-details-marker {
  display: none;
}
summary.report-subcard-summary::before {
  content: "▸";
  position: absolute;
  left: 0.88rem;
  top: 0.9rem;
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--accent);
  line-height: 1;
}
details.report-subcard[open] > summary.report-subcard-summary::before {
  content: "▾";
}
.report-subcard--bk summary.report-subcard-summary::before {
  color: var(--ci);
}
.report-subcard--bk-fail summary.report-subcard-summary::before {
  color: var(--dashboard-warning);
}
.report-subcard--perf summary.report-subcard-summary::before {
  color: var(--dashboard-violet);
}
.report-subcard--local-fail summary.report-subcard-summary::before {
  color: var(--danger-strong);
}
.report-subcard-body {
  padding: 1rem 1.2rem 1.2rem;
  background: var(--dashboard-panel-bg);
}
.report-subcard-body > .table-scroll:first-child {
  margin-top: 0;
}
.local-summary-pillar-body {
  padding: 0.35rem 0.15rem 0.65rem;
}
details.local-summary-pillar {
  margin-bottom: 0.75rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--dashboard-border);
  background: color-mix(in srgb, var(--dashboard-panel-bg) 90%, var(--accent) 10%);
}
details.local-summary-pillar:last-child {
  margin-bottom: 0;
}
summary.local-summary-pillar-summary {
  list-style: none;
  cursor: pointer;
  padding: 0.55rem 0.85rem 0.55rem 2rem;
  position: relative;
  font-weight: 750;
  font-size: 0.98rem;
  color: var(--dashboard-text);
  background: var(--dashboard-panel-strong);
  border-bottom: 1px solid var(--dashboard-border);
}
summary.local-summary-pillar-summary::-webkit-details-marker {
  display: none;
}
summary.local-summary-pillar-summary::before {
  content: "▸";
  position: absolute;
  left: 0.52rem;
  top: 0.62rem;
  font-size: 0.92rem;
  font-weight: 800;
  color: var(--accent);
  line-height: 1;
}
details.local-summary-pillar[open] > summary.local-summary-pillar-summary::before {
  content: "▾";
}
details.local-summary-dim {
  margin: 0.5rem 0.35rem 0.45rem 0.65rem;
  border-radius: var(--radius-sm);
  border: 1px dashed color-mix(in srgb, var(--dashboard-border) 82%, var(--accent) 18%);
  background: var(--dashboard-panel-bg);
}
summary.local-summary-dim-summary {
  list-style: none;
  cursor: pointer;
  padding: 0.42rem 0.75rem 0.42rem 1.85rem;
  position: relative;
  font-weight: 680;
  font-size: 0.9rem;
  color: var(--dashboard-muted);
  background: color-mix(in srgb, var(--dashboard-panel-bg) 96%, var(--accent) 4%);
  border-bottom: 1px solid var(--dashboard-border);
}
summary.local-summary-dim-summary::-webkit-details-marker {
  display: none;
}
summary.local-summary-dim-summary::before {
  content: "▸";
  position: absolute;
  left: 0.45rem;
  top: 0.48rem;
  font-size: 0.85rem;
  font-weight: 800;
  color: var(--accent);
  line-height: 1;
}
details.local-summary-dim[open] > summary.local-summary-dim-summary::before {
  content: "▾";
}
.local-summary-dim-body {
  padding: 0.55rem 0.45rem 0.65rem;
}
.local-summary-dim-body > .table-scroll:first-child {
  margin-top: 0;
}
.ico {
  display: block;
}
"""

# Scoped rules for release Markdown → HTML (compose_full_report body).
RELEASE_MARKDOWN_DOC_CSS = """
.top-bar-actions {
  flex-shrink: 0;
}
.btn-release-archive {
  margin-top: 0.2rem;
  padding: 0.52rem 1.05rem;
  border-radius: 999px;
  border: 1px solid rgba(59, 130, 246, 0.35);
  background: rgba(59, 130, 246, 0.12);
  color: var(--accent-hover);
  font-weight: 700;
  font-size: 0.88rem;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}
.btn-release-archive:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: var(--accent);
  color: var(--accent);
}
.release-doc.panel {
  margin-bottom: 0;
}
.release-doc.panel:hover {
  box-shadow: var(--dashboard-shadow);
  border-color: var(--dashboard-border);
}
.release-doc > .meta.generated-meta {
  margin: 0 0 1rem;
  padding-bottom: 0.85rem;
  border-bottom: 1px dashed color-mix(in srgb, var(--dashboard-border-strong) 55%, transparent);
}
.release-doc h2 {
  margin: 1.35rem 0 0.75rem;
  font-size: 1.12rem;
  font-weight: 800;
  color: var(--dashboard-text);
  letter-spacing: -0.02em;
  border-bottom: 2px solid var(--dashboard-border);
  padding-bottom: 0.55rem;
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
.release-doc h2:first-of-type {
  margin-top: 0;
}
.release-doc h3 {
  margin: 1.15rem 0 0.55rem;
  font-size: 1.04rem;
  color: var(--dashboard-soft-text);
  font-weight: 700;
}
.release-doc h4, .release-doc h5, .release-doc h6 {
  margin: 1rem 0 0.45rem;
  font-size: 1rem;
  color: var(--dashboard-soft-text);
  font-weight: 700;
}
.release-doc p {
  margin: 0.65rem 0;
}
.release-doc p:first-of-type {
  margin-top: 0;
}
.release-doc ul {
  margin: 0.5rem 0 0.85rem 1.25rem;
  padding: 0;
}
.release-doc li {
  margin: 0.3rem 0;
}
.release-doc .table-scroll {
  margin: 0.85rem 0;
}
.release-doc .table-scroll > table {
  min-width: 480px;
}
.release-doc table {
  border-collapse: collapse;
  width: 100%;
  margin: 0;
  font-size: 0.92rem;
}
.release-doc th, .release-doc td {
  border: 1px solid var(--border);
  padding: 0.65rem 0.8rem;
  text-align: left;
  vertical-align: top;
}
.release-doc th {
  background: var(--dashboard-panel-strong);
  font-weight: 650;
  color: var(--dashboard-chart-text);
}
.release-doc tbody tr:nth-child(even) td {
  background: color-mix(in srgb, var(--dashboard-badge-bg) 45%, var(--dashboard-panel-bg));
}
.release-doc code {
  background: color-mix(in srgb, var(--dashboard-badge-bg) 55%, var(--dashboard-panel-bg));
  padding: 0.12em 0.38em;
  border-radius: 4px;
  font-size: 0.92em;
  font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
}
.release-doc a {
  color: var(--accent);
  font-weight: 600;
  text-decoration: none;
  border-bottom: 1px solid var(--accent-soft);
}
.release-doc a:hover {
  color: var(--accent-hover);
  border-bottom-color: var(--accent);
}
.release-conclusion-wrap {
  margin: 0.5rem 0 1rem;
}
.release-conclusion-table {
  min-width: 320px;
}
.release-conclusion-table td:last-child {
  white-space: normal;
}
.conc-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  align-items: center;
}
.conc-btns.conc-auto {
  pointer-events: none;
  opacity: 0.9;
}
.conc-auto-hint {
  margin-top: 0.35rem;
  font-size: 0.82rem;
  line-height: 1.35;
  color: color-mix(in srgb, var(--dashboard-text) 65%, transparent);
}
.conc-btn {
  font: inherit;
  font-size: 0.86rem;
  font-weight: 650;
  padding: 0.38rem 0.95rem;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid var(--border);
  background: color-mix(in srgb, var(--dashboard-panel-bg) 88%, var(--dashboard-badge-bg));
  color: var(--dashboard-text);
  transition: background 0.12s ease, border-color 0.12s ease, color 0.12s ease;
}
.conc-btn:hover {
  border-color: var(--accent-soft);
}
.conc-btn.conc-pass.is-on {
  background: color-mix(in srgb, #16a34a 22%, var(--dashboard-panel-bg));
  border-color: color-mix(in srgb, #16a34a 45%, var(--border));
  color: #15803d;
}
.conc-btn.conc-fail.is-on {
  background: color-mix(in srgb, #dc2626 20%, var(--dashboard-panel-bg));
  border-color: color-mix(in srgb, #dc2626 42%, var(--border));
  color: #b91c1c;
}
.release-verdict-line {
  margin: 1rem 0 0.25rem;
  font-size: 1.02rem;
  font-weight: 650;
}
.release-verdict {
  font-weight: 800;
  letter-spacing: 0.02em;
}
"""
