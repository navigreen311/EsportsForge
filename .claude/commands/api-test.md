# api-test — Generate API Contract & Integration Tests

Generate API contract and integration tests from OpenAPI/GraphQL specs or live endpoints.

## Arguments

$ARGUMENTS

Parse the following from the arguments:

| Argument            | Required | Default      | Description                                          |
|---------------------|----------|--------------|------------------------------------------------------|
| `spec_path_or_url`  | Yes      | —            | Path to OpenAPI/GraphQL spec file, or base URL        |
| `auth_mode`         | No       | `none`       | Auth type: `none`, `bearer`, `api-key`, `basic`, `oauth2` |
| `env`               | No       | `local`      | Target environment: `local`, `staging`, `production`   |
| `test_style`        | No       | `supertest`  | Test runner: `supertest`, `axios`, `fetch`, `playwright` |
| `load_smoke`        | No       | `false`      | Include basic load/smoke test: `true` or `false`       |

---

## Process

### Step 1: Parse Spec / Discover Endpoints
1. If `spec_path_or_url` is an OpenAPI/Swagger file:
   - Parse all routes, methods, request/response schemas.
   - Extract authentication requirements.
   - Note required vs optional parameters.

2. If `spec_path_or_url` is a GraphQL schema:
   - Parse queries, mutations, subscriptions.
   - Extract input/output types.

3. If `spec_path_or_url` is a base URL:
   - Attempt to discover `/docs`, `/swagger.json`, `/openapi.json`.
   - Fall back to manually specified routes.

### Step 2: Generate Test Cases
For each endpoint, generate:

**Success Tests (2xx)**
- Happy path with valid data
- All optional parameters included
- Minimum required parameters only
- Pagination / filtering if applicable

**Error Tests (4xx/5xx)**
- Missing required fields → 400
- Invalid data types → 400/422
- Unauthorized access → 401
- Forbidden access → 403
- Resource not found → 404
- Duplicate/conflict → 409

**Edge Cases**
- Empty strings, null values
- Maximum length inputs
- Special characters / unicode
- Empty arrays / objects

### Step 3: Create Reusable Test Helpers
Create `tests/api/helpers/`:
- `client.ts` — configured HTTP client with base URL and auth
- `fixtures.ts` — test data factories
- `assertions.ts` — custom assertion helpers
- `setup.ts` — before/after hooks, DB seeding, cleanup

### Step 4: Environment CLI
Create test configuration for multiple environments:
```
tests/api/
  config/
    local.env
    staging.env
  helpers/
  endpoints/
    users.test.ts
    auth.test.ts
    ...
```

Provide npm scripts or commands:
- `test:api` — run all API tests against local
- `test:api:staging` — run against staging
- `test:api:single -- <file>` — run single test file

### Step 5: Load/Smoke Test (if `load_smoke=true`)
1. Create a basic load test using `autocannon`, `k6`, or `artillery`.
2. Target: key endpoints at low concurrency (smoke level).
3. Report: avg latency, p95, p99, error rate.

### Step 6: Run & Summarize

```
## API TEST RESULTS

### Endpoints Covered
| Method | Path              | Tests | Pass | Fail |
|--------|-------------------|-------|------|------|
| GET    | /api/users        | 5     | 5    | 0    |
| POST   | /api/users        | 8     | 7    | 1    |
| ...    | ...               | ...   | ...  | ...  |

### Summary
- Total tests: X
- Passed: X
- Failed: X
- Coverage: X endpoints / Y total

### Failed Tests
- [details of any failures]

### HOW TO RUN
- All API tests: `[command]`
- Single file: `[command]`
- With coverage: `[command]`

### FILES CREATED
- [list of test files and helpers]
```

---

## Example Invocation

```
/api-test spec_path_or_url=./openapi.yaml auth_mode=bearer env=local test_style=supertest load_smoke=true
```
