# Search Strategies for PR Mining

## GitHub Search Query Patterns

### By Title Prefix (vLLM-Omni convention)

vLLM-Omni uses title prefixes like `[Model]`, `[Bugfix]`, `[Feature]`, etc.

```bash
# Exact prefix match
gh pr list --repo vllm-project/vllm-omni --state merged \
  --search "in:title [Model]" --limit 50 \
  --json number,title,url,comments,createdAt

# Multiple prefix variants
gh pr list --repo vllm-project/vllm-omni --state merged \
  --search "in:title [Model] OR in:title [Feature] add model" --limit 50 \
  --json number,title,url,comments,createdAt
```

### By Label

```bash
# Label-based search (vLLM upstream uses labels extensively)
gh pr list --repo vllm-project/vllm --state merged \
  --label "new-model" --limit 50 \
  --json number,title,url,comments,createdAt

# Combined label + keyword
gh pr list --repo vllm-project/vllm --state merged \
  --label "new-model" --search "support" --limit 50 \
  --json number,title,url,comments,createdAt
```

### By Changed Files (via GitHub Search API)

```bash
# Search for PRs touching specific directories
gh api search/issues \
  --method GET \
  -f q="repo:vllm-project/vllm is:pr is:merged path:vllm/model_executor/models/" \
  --jq '.items[] | {number, title, html_url}'
```

### By Review Activity (filter for substantive reviews)

```bash
# Get PR list, then filter by review count
gh pr list --repo vllm-project/vllm --state merged \
  --search "<query>" --limit 100 \
  --json number,title,reviewDecision,comments | \
  jq '[.[] | select(.comments > 3)]'
```

## Filtering for High-Quality Reviews

Not all PRs have useful review comments. Prioritize:

1. **PRs with "changes requested" reviews** — these contain the most actionable feedback
2. **PRs with 5+ review comments** — indicate thorough review
3. **PRs from experienced reviewers** — look for reviews from maintainers or core contributors
4. **PRs that went through multiple review rounds** — the back-and-forth reveals important patterns

```bash
# Fetch reviews for a specific PR and filter for substantive ones
gh api repos/vllm-project/vllm/pulls/<number>/reviews \
  --jq '[.[] | select(.state == "CHANGES_REQUESTED" or (.body | length > 50))]'

# Count inline comments per PR
gh api repos/vllm-project/vllm/pulls/<number>/comments \
  --jq 'length'
```

## Cross-Repo Search Strategy

When mining from both repos, use this priority order:

1. **vLLM-Omni PRs first** — most directly relevant, same codebase conventions
2. **vLLM upstream PRs** — larger volume, more review history, general patterns
3. **Cross-reference** — note patterns that appear in both repos (these are highest signal)

### Recommended PR Counts by Category

| Category | vLLM-Omni Target | vLLM Target | Minimum Viable |
|----------|------------------|-------------|----------------|
| New model | 5-10 | 10-20 | 8 total |
| Bugfix | 5-10 | 10-15 | 8 total |
| Performance | 3-5 | 5-10 | 5 total |
| Diffusion | 5-10 | 0-3 | 5 total |
| TTS/Audio | 3-5 | 0-2 | 3 total |

## Handling Pagination

```bash
# For large result sets, paginate
gh api repos/vllm-project/vllm/pulls \
  --method GET \
  -f state=closed \
  -f per_page=100 \
  -f page=1 \
  --jq '.[] | select(.merged_at != null) | {number, title}'
```

## Rate Limit Awareness

```bash
# Check current rate limit
gh api rate_limit --jq '.resources.core | {remaining, reset: (.reset | todate)}'
```

If remaining < 100, pause and inform the user. Each PR analysis uses approximately:
- 1 call for PR metadata
- 1 call for review comments
- 1 call for inline comments
- 1 call for issue comments

So 20 PRs ≈ 80 API calls.
