# Review Comment Analysis & Classification Guide

## Comment Classification Categories

When processing review comments from PRs, classify each comment into one of these categories:

### 1. Correctness Issues
Comments about bugs, logic errors, or incorrect behavior.

**Signal words:** "this will break", "bug", "incorrect", "wrong", "doesn't handle", "edge case", "race condition", "undefined behavior"

**Example patterns:**
- "This doesn't handle the case where `input_ids` is empty"
- "Race condition: `self.cache` can be modified by another thread here"
- "Off-by-one error in the loop bound"

### 2. Missing Tests
Comments requesting test coverage.

**Signal words:** "test", "coverage", "assert", "verify", "regression", "unit test", "integration test"

**Example patterns:**
- "Please add a test for the new code path"
- "Can you add a regression test for this fix?"
- "This needs an integration test with the actual model"

### 3. Performance Concerns
Comments about efficiency, memory, latency, or scalability.

**Signal words:** "performance", "memory", "slow", "optimize", "batch", "latency", "throughput", "allocation", "copy", "overhead"

**Example patterns:**
- "This creates a new tensor on every forward pass — consider caching"
- "Unnecessary copy here, use in-place operation"
- "This won't scale with large batch sizes"

### 4. API/Interface Design
Comments about public interfaces, backward compatibility, configuration.

**Signal words:** "breaking change", "backward compatible", "API", "interface", "config", "parameter", "deprecate", "public"

**Example patterns:**
- "This changes the public API — needs a deprecation path"
- "New config parameter needs validation and documentation"
- "This should be exposed as an optional parameter, not hardcoded"

### 5. Architecture/Design
Comments about code organization, patterns, and design decisions.

**Signal words:** "design", "architecture", "refactor", "pattern", "abstraction", "coupling", "separation of concerns", "responsibility"

**Example patterns:**
- "This logic belongs in the stage, not the connector"
- "Consider extracting this into a utility function"
- "This breaks the separation between AR and diffusion stages"

### 6. Error Handling
Comments about exception handling, validation, and failure modes.

**Signal words:** "error", "exception", "validate", "check", "handle", "fallback", "graceful", "raise", "assert"

**Example patterns:**
- "What happens if the model download fails here?"
- "This should validate the input shape before processing"
- "Swallowed exception — at minimum log a warning"

### 7. Documentation
Comments requesting or improving documentation.

**Signal words:** "doc", "docstring", "comment", "explain", "readme", "document"

**Example patterns:**
- "Please add a docstring explaining the expected input format"
- "Update the README with the new model"
- "This complex logic needs an inline comment"

### 8. Security
Comments about security vulnerabilities or unsafe practices.

**Signal words:** "security", "injection", "sanitize", "escape", "permission", "auth", "credential", "unsafe"

**Example patterns:**
- "User input is passed directly to the shell — needs sanitization"
- "This exposes internal paths in the error message"

### 9. Code Style / Convention
Lower-priority comments about style, naming, or conventions.

**Signal words:** "style", "naming", "convention", "consistent", "typo", "nit", "minor"

**Example patterns:**
- "nit: variable name should follow snake_case"
- "This doesn't follow the existing pattern in other models"

## Aggregation Strategy

After classifying all comments:

### Frequency Analysis
1. Count occurrences of each category across all PRs
2. Rank categories by frequency
3. Identify the top 5 most common issue types

### Pattern Extraction
For each high-frequency category:
1. Group similar comments together
2. Extract the common underlying rule or principle
3. Write a concise, actionable checklist item
4. Include 1-2 concrete examples from the actual reviews

### Cross-PR Patterns
Look for:
- **Same reviewer, same comment across PRs** → likely a project convention or policy
- **Multiple reviewers, same comment** → strong consensus, high-priority rule
- **Comment leads to code change** → validated feedback (vs. discussion-only comments)
- **Comment appears in both vLLM and vLLM-Omni** → fundamental/universal pattern

### Weighting

Assign weights to review comments:

| Signal | Weight |
|--------|--------|
| Comment led to code change (resolved) | 3x |
| Comment from maintainer/core reviewer | 2x |
| Comment appears in 3+ PRs | 2x |
| Comment appears in both repos | 2x |
| "Changes requested" review | 1.5x |
| Comment is a "nit" or "minor" | 0.5x |
| Comment was disagreed with / not applied | 0.3x |

### Output Format

For each extracted pattern, produce:

```markdown
### [Pattern Name]

**Frequency:** Found in X/Y PRs analyzed
**Category:** [Correctness | Tests | Performance | ...]
**Severity:** [Blocking | Important | Nice-to-have]

**Rule:** [One-sentence actionable rule]

**What to look for:**
- [Specific code pattern or condition to check]
- [Another thing to check]

**Example from review:**
> [Quoted review comment]
> — PR #NNN
```

## Special Handling

### Conversational Threads
When a review comment spawns a discussion:
- Track the full thread, not just the initial comment
- The resolution (final state) is more important than the initial ask
- If the author pushed back and the reviewer agreed, the original comment may not be a pattern

### Bot / CI Comments
- Skip automated comments (CI bots, linters, etc.)
- These don't represent human review patterns

### Stale Comments
- Deprioritize comments from PRs older than 12 months
- Coding standards and conventions evolve
