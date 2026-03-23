# code-review — Structured Example-Driven Code Review

Perform a structured, example-driven code review covering architecture, correctness, security, performance, and maintainability.

## Arguments

$ARGUMENTS

Parse the following from the arguments:

| Argument             | Required | Default      | Description                                          |
|----------------------|----------|--------------|------------------------------------------------------|
| `paths`              | Yes      | —            | File paths or directories to review                   |
| `style_examples`     | No       | —            | Paths to exemplary files to match style against        |
| `severity_threshold` | No       | `info`       | Minimum severity to report: `info`, `warning`, `error` |

---

## Process

### Step 1: Learn Style from Examples
If `style_examples` are provided:
1. Read each example file carefully.
2. Identify the core design principles, coding style, naming conventions, and architectural patterns.
3. Use these as the baseline for the review.

If no examples provided:
1. Read the project's existing code to understand prevailing style.
2. Check for linter configs, prettier configs, or style guides in the repo.

### Step 2: Review Against Checklist

For each file in `paths`, evaluate against these dimensions:

**Architecture & Design**
- [ ] Single responsibility — does each module/function do one thing?
- [ ] Appropriate abstractions — not over-engineered, not under-abstracted?
- [ ] Clear boundaries between layers/modules?
- [ ] Consistent with project architecture patterns?

**Correctness**
- [ ] Logic is sound and handles all cases?
- [ ] Edge cases and error paths covered?
- [ ] Types/contracts are correct?
- [ ] No off-by-one, null reference, or race condition issues?

**Security**
- [ ] No hardcoded secrets or credentials?
- [ ] Input validation and sanitization present?
- [ ] Authentication/authorization checks where needed?
- [ ] SQL injection, XSS, CSRF protections?
- [ ] Sensitive data not logged or exposed?

**Performance**
- [ ] No unnecessary re-renders, N+1 queries, or blocking calls?
- [ ] Appropriate caching, pagination, lazy loading?
- [ ] Resource cleanup (connections, file handles, listeners)?

**Maintainability**
- [ ] Clear naming (variables, functions, files)?
- [ ] Appropriate comments (why, not what)?
- [ ] Tests exist and are meaningful?
- [ ] Easy to modify without ripple effects?

**Style Compliance**
- [ ] Matches example file conventions?
- [ ] Consistent formatting, imports, exports?
- [ ] Follows project linter/formatter rules?

### Step 3: Produce Issues

For each finding, output:

```
### [SEVERITY] [Category]: [Short Title]
**File:** `path/to/file.ext:LINE`
**Issue:** Description of the problem.
**Suggestion:** How to fix it.
**Patch:**
```diff
- old code
+ new code
```
```

### Step 4: Summary by Severity

```
## REVIEW SUMMARY

| Severity | Count |
|----------|-------|
| Error    | X     |
| Warning  | X     |
| Info     | X     |

### Critical Issues (must fix)
- [list]

### Recommended Improvements
- [list]

### Positive Observations
- [what's done well — always include this]
```

### Step 5: PR-Ready Comment
Output a ready-to-paste PR review comment with all findings formatted for GitHub/GitLab.

---

## Example Invocation

```
/code-review paths=src/services/ style_examples=src/services/auth.service.ts severity_threshold=warning
```
