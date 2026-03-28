# CI testing: GitHub `[CI Failure]` issue list

Data rules and sources for the **### Analysis (CI Failure)** table under **## CI testing** in the report.

## Data sources (manual cross-check / API)

- **Open `label:bug`:** [Issues search (open)](https://github.com/vllm-project/vllm-omni/issues/?q=is%3Aissue%20state%3Aopen%20label%3Abug)
- **Closed `label:bug`:** [Issues search (closed)](https://github.com/vllm-project/vllm-omni/issues/?q=is%3Aissue%20state%3Aclosed%20label%3Abug)

For a full enumeration, use the **GitHub REST API** (`GET /search/issues` or paginated `GET /repos/vllm-project/vllm-omni/issues`); do not rely on the first page of the web UI alone.

## Filter rules

| Criterion | Description |
|-----------|-------------|
| **Label** | `bug` |
| **Title prefix** | Starts with **`[CI Failure]`** (the six letters inside the brackets are **case-insensitive**, e.g. `[ci failure]`, `[CI FAILURE]`); or **`[Bug]: [CI Failure]…`** (`[Bug]` and the colon are case/spacing insensitive; second tag follows the same rule). |
| **Time** | **`created_at`** (UTC) falls in the **report month** (`YYYY-MM` prefix, aligned with Metrics / Open issues). |
| **Exclude** | PR entries (`pull_request` non-null). |

## Table columns

| Column | Content |
|--------|---------|
| **Issue #** | Link to `https://github.com/vllm-project/vllm-omni/issues/{n}` |
| **Title** | Issue `title` (escape `\|` in Markdown if needed) |
| **Status** | **Open** (`state=open`) or **Closed** (`state=closed`) |

If nothing matches in the month: add a short note (e.g. *No `label:bug` issues with a case-insensitive `[CI Failure]` title prefix this month*)—do not leave an empty table.
