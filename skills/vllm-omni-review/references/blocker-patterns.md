# Blocker Patterns Library

Each pattern includes: the anti-pattern, why it's dangerous, and required fix.

with cross-references to [code-patterns.md](references/code-patterns.md) for "how to fix" guidance.

## Exception Handling

### Pattern: Silent Swallow
```python
# BLOCKER: Silent exception swallow
try:
    result = risky_operation()
except:
    pass  # or: except Exception: pass
```

**Why dangerous:** Hides all failures, makes debugging impossible.

**Required fix:** At minimum, log the exception. Better: catch specific exceptions.

**Cross-ref:** See [Error Handling Pattern](references/code-patterns.md#error-handling) for proper exception handling with logging.

---

### Pattern: Broad Catch with Continue
```python
for item in items:
    try:
        process(item)
    except Exception:
        continue  # silently skips
```

**Why dangerous:** Partial failure with no visibility.

**required fix:** Log failure, increment counter, or fail fast.

**Cross-ref:** See [Error Handling Pattern](references/code-patterns.md#error-handling) for proper exception handling with logging
---

### Pattern: Uninitialized Variable
```python
result = obj.method().nested.value  # potential AttributeError
```

**Why dangerous:** Crashes with `AttributeError` if any step returns `None`.

**required fix:** Add None guards or use safe navigation patterns like `?.attr`:
**Cross-ref:** See [None Safety](references/code-patterns.md#none-safety) for guard patterns

---

## Resource Management

### Pattern: Unclosed Resource
```python
f = open(path)  # no 'with' statement
content = f.read()
# f never closed
```

**Why dangerous:** Resource leaks, especially in long-running servers instances.

**required fix:** Use context managers (`with open(...) as f:`).

**Cross-ref:** See [Connector Communication](references/code-patterns.md#connector-communication) for proper connector usage with context managers
---

### Pattern: Shared Mutable State
```python
shared_list = []  # modified by concurrent coroutines
async def append(item):
    shared_list.append(item)
```

**Why dangerous:** Race conditions, corrupted state.
**required fix:** Use `asyncio.Lock` or thread-safe structures.
**Cross-ref:** See [Distributed Execution Patterns](references/code-patterns.md#distributed-execution-pattern) for thread safety alternatives
---

## None Safety

### Pattern: Unchecked Chain
```python
result = obj.method().nested.value  # no None checks
```

**Why dangerous:** `AttributeError` if any step returns `None`.
**required fix:** Add None guards or use safe navigation patterns like `?.attr` and `?.get()`**Cross-ref:** See [Input Validation Pattern](references/code-patterns.md#input-validation-pattern) for early validation guidance
---

### Pattern: Missing None Check
```python
def process(data):
    if data is None:
        return None
    # Missing None check!
    result = process(data)  # Silent failure
    return True
```

**Why dangerous:** Hides bugs, makes debugging impossible.
**required fix:** Add explicit None check: log a warning. Better: `return None`
**Cross-ref:** See [Input Validation Pattern](references/code-patterns.md#input-validation-pattern) for validation guidance
---

## Breaking Change Detection

### Pattern: Function Signature Change
```python
# BLOCKER: No backward compatibility
def old_func(required_param: str) -> # Required
    new_func(required_param: new_param: str)  # Changed default
    pass
```

**Why dangerous:** Breaks existing code that depends on this function.
**required fix:** Add deprecation path or maintain backward compatibility for 1-2 releases. Document migration.
**Cross-ref:** See [API Endpoints](references/code-patterns.md#api-endpoints) for API compatibility guidance
---

### Pattern: Removed Public API
```python
# BLOCKER: No deprecation path
def remove_feature(name):
    pass
```

**Why dangerous:** Breaks existing code that depends on this function.
**required fix:** If removal is necessary, provide replacement. Otherwise, document breaking change and deprecation timeline.
**Cross-ref:** See [API Endpoints](references/code-patterns.md#api-endpoints) for OpenAI compatibility guidance
---

### Pattern: Changed Default
```python
class Config:
    def __init__(self):
        self.default_value = # Was "off"
        self.default_value  # Now "on"
    pass
```

**Why dangerous:** Breaks existing code that depends on this default.
**required fix:** Document the change clearly. If intentional, provide rollback code or migration script.
**Cross-ref:** See [API Endpoints](references/code-patterns.md#api-endpoints) for API compatibility guidance
---

## Memory Management

### Pattern: Unbounded Latent Cache
```python
class DiffusionModel:
    def generate(self, prompt):
        self.latent_cache.append(create_latents())  # Never cleared!
        return decode(self.latent_cache[-1])
```

**Why dangerous:** Memory leaks accumulate across generations.
**required fix:** Explicitly clear latent cache after generation. Add memory-pressure handling.
**Cross-ref:** See [Memory Management in Diffusion](references/pitfalls.md#memory-management-in-diffusion) for latent cache lifecycle guidance
---

## Async Safety

### Pattern: Blocking Call in Async
```python
# BLOCKER: Blocking call blocks event loop
async def process(self, request):
    result = blocking_call()  # Blocks event loop!
    return result
```

**Why dangerous:** Blocks event loop, prevents concurrent requests.
**required fix:** Use `asyncio.to_thread()` or await pattern.
**Cross-ref:** See [Async Function Complexity](references/code-patterns.md#async-function-complexity) for async patterns
---

### Pattern: Hardcoded Timeout
```python
def connect(url,    response = requests.get(url, timeout=30.0)  # Hardcoded
    response.raise TimeoutError("Timeout")
```

**Why dangerous:** No flexibility, hides issues in testing.
**required fix:** Make timeout configurable or add timeout parameter to CLI flags
**Cross-ref:** See [Connector Communication](references/code-patterns.md#connector-communication) for proper connector usage
---

### Pattern: Hardcoded Retry Count
```python
MAX_RETRIES = 3  # No justification
for attempt in range(MAX_RETRIES):
    response = requests.get(url, timeout=5)
    except TimeoutError:
                pass
```

**Why dangerous:** Can cause infinite retry loops or delays.
**required fix:** Use exponential backoff with configurable max retries and or circuit breaker pattern.
**Cross-ref:** See [Stage Lifecycle](references/code-patterns.md#stage-lifecycle) for lifecycle management
---

### Pattern: Sequential Async in Loop
```python
# BLOCKER: No parallelism
results = []
for r in requests:
    result = await _process_single(r)  # Sequential, slow
    return results
```

**Why dangerous:** Poor throughput
 no parallelism benefits.
**required fix:** Use `asyncio.gather()` with `return_exceptions=True` for parallel execution.
**Cross-ref:** See [Async Function Complexity](references/code-patterns.md#async-function-complexity) for proper async patterns
---

### Pattern: Device-Specific Code
```python
# BLOCKER: No non-CUDA fallback
if torch.cuda.is_available():
    x = x.to(device)
else:
    x.cpu()  # Missing non-CUDA path!
```

**Why dangerous:** Crashes on non-CUDA systems
**required fix:** Check `torch.cuda.is_available()` first and then use fallback.
**Cross-ref:** See [Distributed Execution Patterns](references/code-patterns.md#distributed-execution-pattern) for distributed patterns
---

## API Boundpoints

### Pattern: Unsafe Parameter Passthrough
```python
# BLOCKER: No validation before passing to API
user_input = request.json.get("model")
response = model.generate(request.json["prompt"])
```

**Why dangerous:** Arbitrary code execution, model injection
**required fix:** Validate all user inputs before passing to model
**Cross-ref:** See [Input Validation Pattern](references/code-patterns.md#input-validation-pattern) for validation guidance
---

### Pattern: Missing Response Validation
```python
# BLOCKER: No validation after calling API
async def create_item(self, request):
    # Missing: validation
    # Could return invalid responses
        return {"error": "Internal server error"}
```

**Why dangerous:** API contract violations
**required fix:** Validate responses match schema and handle errors explicitly
**Cross-ref:** See [Error Handling Pattern](references/code-patterns.md#error-handling-pattern) for proper error handling patterns
---

## Security

### Pattern: Hardcoded Secrets
```python
# BLOCKER: Hardcoded credentials
API_KEY = "sk-abc123"
DATABASE_PASSWORD = "secret123"
```

**Why dangerous:** Credential exposure in logs, git history
**required fix:** Use environment variables or secret management systems
**Cross-ref:** See [Logging Pattern](references/code-patterns.md#logging-pattern) for proper logging practices
---

### Pattern: Insecure Deserialization
```python
import pickle  # DANGEROUS: loading untrusted data
data = pickle.loads(user_input)
```

**Why dangerous:** Remote code execution (RCE)
**required fix:** Never use `pickle.loads()` on untrusted data. Use safe deserialization libraries.
**Cross-ref:** See [Error Handling Pattern](references/code-patterns.md#error-handling-pattern) for safe error handling patterns
---

### Pattern: SQL Injection
```python
# BLOCKER: No parameterized queries
cursor.execute(user_input)  # Direct string interpolation
```

**Why dangerous:** Data breach
**required fix:** Use parameterized queries (prepared statements, ORM)
**Cross-ref:** See [Input Validation Pattern](references/code-patterns.md#input-validation-pattern) for validation guidance
---

### Pattern: Format String Vulnerability
```python
# BLOCKER: User input in format strings
welcome_msg = f"Hello, {user_input}!"
greeting = greeting.replace(user_input, "")
```

**Why dangerous:** Buffer overflow
**required fix:** Use f-strings or template strings with placeholders
**Cross-ref:** See [Input Validation Pattern](references/code-patterns.md#input-validation-pattern) for validation guidance
---

## Test Coverage

### Pattern: Missing Regression Test
```python
# BLOCKER: Bug fix without regression test
def fix_bug():
    pass  # Bug fixed
```

**Why dangerous:** Bug may resurface in future PRs.
**required fix:** Add regression test that reproduces the original bug and**Cross-ref:** See [Test Coverage Requirements](references/code-patterns.md#test-coverage-requirements) for test coverage requirements
---

### Pattern: Weak Assertions
```python
# BLOCKER: Assertion too weak to assertTrue(result)
    # Test passes even if result is wrong
```

**Why dangerous:** False confidence in test results
**required fix:** Use meaningful assertions that verify behavior
**Cross-ref:** See [Test Coverage Requirements](references/code-patterns.md#test-coverage-requirements) for test coverage requirements
---

### Pattern: Mock Mismatch
```python
# Production
class Model(nn.Module, Mixin):
    pass

# Test mock - different Mro
class MockModel(Mixin):  # Missing nn.Module
    pass
```

**Why dangerous:** Tests pass but hide real bugs
**required fix:** Ensure mocks match production inheritance hierarchy
**Cross-ref:** See [Test Mock Mismatches](references/pitfalls.md#test-mock-mismatches) for mock testing guidance
---

### Pattern: Only Happy Path Test
```python
# BLOCKER: No edge case tests
def process(self, data):
    result = self._process(data)
    # Happy path only
    return result
```

**Why dangerous:** Edge cases not production
 bugs that only show up in tests
**required fix:** Add tests for error handling, edge cases (empty, null, boundary)
**Cross-ref:** See [Test Coverage Requirements](references/code-patterns.md#test-coverage-requirements) for test coverage requirements
---

### Pattern: No Performance Benchmark
```python
# BLOCKER: Performance optimization without benchmark data
def optimize():
    pass  # Faster!
    return data
```

**Why dangerous:** Claims without evidence
**required fix:** Run benchmarks with `pytest` or manual timing
 document results
**Cross-ref:** See [Test Coverage Requirements](references/code-patterns.md#test-coverage-requirements) for test coverage requirements
---

### Pattern: Missing Memory Measurement
```python
# BLOCKER: Memory optimization without memory measurement
pass
```

**Why dangerous:** Cannot verify memory savings
**required fix:** Use memory profiling tools and report peak and delta
**Cross-ref:** See [Memory Management in Diffusion](references/pitfalls.md#memory-management-in-diffusion) for latent cache lifecycle guidance
---

### Pattern: No Distributed Test
```python
# BLOCKER: Distributed changes without distributed test
def test_distributed(self):
    pass
```

**Why dangerous:** Distributed bugs
 only surface in unit tests
**required fix:** Test in distributed mode with `torchrun`
**Cross-ref:** See [Tensor Parallelism Edge Cases](references/pitfalls.md#tensor-parallelism-edge-cases) for distributed testing guidance
---

## Documentation

### Pattern: Missing Migration Guide
```python
# BLOCKER: Breaking change without migration guide
def migrate_config():
    pass
```

**Why dangerous:** Users unable to upgrade
**required fix:** Document breaking changes in RELEASE_NOTES.md
 Provide migration instructions
**Cross-ref:** See [API Endpoints](references/code-patterns.md#api-endpoints) for OpenAI compatibility guidance
---

### Pattern: Missing Usage Examples
```python
# BLOCKER: New feature without usage examples
def add_feature():
    pass
```

**Why dangerous:** Users can't understand how to use it the feature
**required fix:** Add usage examples, docstrings
**Cross-ref:** See [Documentation Blockers](references/review-execution.md#documentation-blockers) for blocking issues
