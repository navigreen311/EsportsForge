# impl-feature — Plan & Implement a Complete Feature

Implement a complete feature end-to-end: design → code → tests → docs → demo.

## Arguments

$ARGUMENTS

Parse the following from the arguments (use defaults if not provided):

| Argument             | Required | Default      | Description                                      |
|----------------------|----------|--------------|--------------------------------------------------|
| `feature_name`       | Yes      | —            | Kebab-case short name for the feature             |
| `scope`              | Yes      | `fullstack`  | One of: `ui`, `api`, `fullstack`, `agent`, `infra`|
| `acceptance_criteria` | Yes     | —            | Bullet list or Gherkin-style acceptance criteria   |
| `tech_constraints`   | No       | —            | Stack limits, required integrations                |
| `priority`           | No       | `p1`         | One of: `p0` (critical), `p1` (high), `p2` (normal)|
| `perf_targets`       | No       | —            | Performance goals (latency, throughput, etc.)       |
| `security_notes`     | No       | —            | Security or compliance requirements                |

---

## Process

### Step 1: Understand & Plan
1. Summarize the inputs and clarify any ambiguities (Flipped Interaction).
2. Write a **mini-PRD** to `docs/plans/${feature_name}.md`:
   - Problem statement
   - Target users
   - Success metrics
   - Constraints & risks
3. Outline the **architecture**: components, data model, APIs, sequence flows.
4. Define **acceptance tests** derived from the criteria.

### Step 2: Branch & Setup
1. Create and checkout branch: `ai-feature/${feature_name}`
2. If parallel work would help, create a **git worktree** and work inside it.
3. Commit the plan file first: `docs: add plan for ${feature_name}`

### Step 3: Implementation
1. Build across all necessary layers according to `scope`.
2. Keep files modular, well-named, with clear boundaries.
3. Make **atomic Conventional Commits** as you go:
   - `feat: add ${component}` for new code
   - `refactor:` for structural changes
   - `fix:` for corrections during implementation

### Step 4: Tests
1. Create or extend **unit + integration tests** aligned with acceptance criteria.
2. Ensure the test command passes cleanly.
3. Commit: `test: add tests for ${feature_name}`

### Step 5: Verification
1. Build/run the application.
2. Perform local smoke tests.
3. Write a short **demo script** with exact commands and URLs.

### Step 6: Docs
1. Update `README.md` with new setup/usage info.
2. Add `docs/${feature_name}.md` (overview, architecture, endpoints, env vars).
3. Update `CHANGELOG.md` with Added/Changed/Removed entries.
4. Commit: `docs: add documentation for ${feature_name}`

### Step 7: Deliver
Provide a summary block:

```
## IMPLEMENTED
- [list of components/files created or modified]

## TESTED
- [test command]: [pass/fail, coverage info]

## HOW TO RUN
- [exact commands to build, start, and demo the feature]

## TRADEOFFS & FOLLOW-UPS
- [known limitations, future improvements]
```

---

## Error Handling
- On build/test failures: show logs, propose fixes, retry.
- On missing info: make clearly labeled `ASSUMPTION`s and explain how to change later.
- On merge conflicts: resolve carefully, explain each resolution.

---

## Example Invocation

```
/impl-feature feature_name=user-auth scope=fullstack acceptance_criteria="- Users can register with email/password\n- Users can log in and receive a JWT\n- Protected routes require valid JWT\n- Passwords are hashed with bcrypt" priority=p0 security_notes="OWASP top 10 compliance"
```
