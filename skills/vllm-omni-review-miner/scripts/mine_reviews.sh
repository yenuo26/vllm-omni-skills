#!/usr/bin/env bash
# Mine PR review comments from vLLM and vLLM-Omni repos.
#
# Usage:
#   ./mine_reviews.sh <search_query> [output_dir] [limit]
#
# Examples:
#   ./mine_reviews.sh "[Model]" ./output 20
#   ./mine_reviews.sh "add support for" ./output 15
#   ./mine_reviews.sh "[TTS]" ./output 10

set -euo pipefail

SEARCH_QUERY="${1:?Usage: mine_reviews.sh <search_query> [output_dir] [limit]}"
OUTPUT_DIR="${2:-./review_mining_output}"
LIMIT="${3:-20}"

REPOS=("vllm-project/vllm" "vllm-project/vllm-omni")

mkdir -p "$OUTPUT_DIR"

echo "=== Review Mining Started ==="
echo "Query: $SEARCH_QUERY"
echo "Output: $OUTPUT_DIR"
echo "Limit per repo: $LIMIT"
echo ""

# Check rate limit
echo "--- GitHub API Rate Limit ---"
gh api rate_limit --jq '.resources.core | "Remaining: \(.remaining) | Resets: \(.reset | todate)"'
echo ""

for REPO in "${REPOS[@]}"; do
    REPO_SHORT=$(echo "$REPO" | tr '/' '_')
    echo "=== Mining $REPO ==="

    # Fetch merged PRs matching the query
    PR_FILE="$OUTPUT_DIR/${REPO_SHORT}_prs.json"
    gh pr list --repo "$REPO" \
        --state merged \
        --search "$SEARCH_QUERY" \
        --limit "$LIMIT" \
        --json number,title,url,comments,createdAt,mergedAt \
        > "$PR_FILE" 2>/dev/null || {
            echo "Warning: Failed to fetch PRs from $REPO, skipping..."
            continue
        }

    PR_COUNT=$(jq 'length' "$PR_FILE")
    echo "Found $PR_COUNT merged PRs"

    if [ "$PR_COUNT" -eq 0 ]; then
        echo "No PRs found, skipping..."
        continue
    fi

    # For each PR, fetch review comments
    COMMENTS_DIR="$OUTPUT_DIR/${REPO_SHORT}_comments"
    mkdir -p "$COMMENTS_DIR"

    jq -r '.[].number' "$PR_FILE" | while read -r PR_NUM; do
        echo "  Fetching reviews for PR #$PR_NUM..."

        # Inline review comments (code-level)
        gh api "repos/$REPO/pulls/$PR_NUM/comments" \
            --jq '.[] | {body, path, diff_hunk, user: .user.login, created_at}' \
            > "$COMMENTS_DIR/pr_${PR_NUM}_inline.json" 2>/dev/null || true

        # Top-level review bodies
        gh api "repos/$REPO/pulls/$PR_NUM/reviews" \
            --jq '.[] | select(.body != null and .body != "") | {body, state, user: .user.login}' \
            > "$COMMENTS_DIR/pr_${PR_NUM}_reviews.json" 2>/dev/null || true

        # Issue-style discussion comments
        gh api "repos/$REPO/issues/$PR_NUM/comments" \
            --jq '.[] | {body, user: .user.login, created_at}' \
            > "$COMMENTS_DIR/pr_${PR_NUM}_discussion.json" 2>/dev/null || true

        # Small delay to be polite to GitHub API
        sleep 0.5
    done

    echo "Done with $REPO"
    echo ""
done

echo "=== Mining Complete ==="
echo "Output saved to: $OUTPUT_DIR"
echo ""
echo "Files:"
find "$OUTPUT_DIR" -type f -name "*.json" | head -20
echo ""
echo "Next: Analyze the collected comments to extract review patterns."
