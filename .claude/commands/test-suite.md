# test-suite — Create or Extend Automated Test Suite

Create or extend an automated test suite (unit, integration, e2e) and optionally wire it into CI.

## Arguments

$ARGUMENTS

Parse the following from the arguments:

| Argument        | Required | Default       | Description                                        |
|-----------------|----------|---------------|----------------------------------------------------|
| `target`        | Yes      | —             | File, module, or feature to test                    |
| `coverage_goal` | No       | `80%`         | Target code coverage percentage                     |
| `test_kinds`    | No       | `unit,integration` | Comma-separated: `unit`, `integration`, `e2e`  |
| `ci_provider`   | No       | —             | CI platform: `github-actions`, `gitlab-ci`, `none`  |
| `seed_data`     | No       | —             | Path to seed/fixture data or instructions            |

---

## Process

### Step 1: Inventory Existing Tests
1. Scan the project for existing test files, frameworks, and configurations.
2. Identify the testing stack (Jest, Vitest, Pytest, Go test, etc.).
3. List current coverage and any existing CI test jobs.

### Step 2: Gap Analysis
1. Compare existing test coverage against the `target`.
2. Identify untested paths: happy paths, error cases, edge cases, boundary conditions.
3. Prioritize gaps by risk and impact.

### Step 3: Write Tests
For each `test_kind` requested:

**Unit Tests:**
- Test individual functions/methods in isolation.
- Mock external dependencies.
- Cover: normal inputs, edge cases, error conditions.

**Integration Tests:**
- Test component interactions and data flow.
- Use real (or containerized) dependencies where practical.
- Cover: API contracts, database operations, service communication.

**E2E Tests:**
- Test complete user workflows.
- Use appropriate tooling (Playwright, Cypress, Supertest).
- Cover: critical user journeys, authentication flows.

### Step 4: Fixtures & Teardown
1. Create test fixtures and seed data as needed.
2. Ensure proper setup/teardown to avoid test pollution.
3. Place fixtures in `tests/fixtures/` or equivalent.

### Step 5: Test Scripts
1. Add or update npm/make/script commands for running tests:
   - `test` — run all tests
   - `test:unit` — unit tests only
   - `test:integration` — integration tests only
   - `test:e2e` — e2e tests only
   - `test:coverage` — run with coverage report
2. Ensure scripts are idempotent and documented.

### Step 6: CI Configuration (if `ci_provider` specified)
1. Create or update CI workflow file.
2. Include: install → lint → test → coverage upload.
3. Add status badges to README if appropriate.

### Step 7: Run & Summarize
1. Execute the full test suite.
2. Report results:

```
## TEST RESULTS
- Unit:        [X passed / Y total]
- Integration: [X passed / Y total]
- E2E:         [X passed / Y total]
- Coverage:    [X%] (goal: ${coverage_goal})

## NEW TESTS ADDED
- [list of test files created/modified]

## HOW TO RUN
- [exact commands]

## CI STATUS
- [CI config file path, if created]
```

---

## Example Invocation

```
/test-suite target=src/services/auth coverage_goal=90% test_kinds=unit,integration ci_provider=github-actions
```
