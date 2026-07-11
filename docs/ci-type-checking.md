# Static Type-Checking & Linting

Repo-wide reference for how every code area is statically checked in CI, what
strictness is enabled (and what was deliberately skipped), and the conventions for
fixing violations.

Every Python area is checked with **flake8 + mypy**; the frontend (TypeScript) is
checked with **ESLint + `tsc`** — mypy is Python-only, so `tsc --noEmit` is its
analog there. All checks run on push/PR to `main` (`.github/workflows/ci.yml`).

## Coverage at a glance

| Area | Path | Lint job | Style (flake8/ESLint) | Types (mypy/tsc) |
|---|---|---|---|---|
| Backend | `backend/` (`app/` + `tests/`) | `Lint Backend` | flake8, 120 cols | mypy **strict** (+ pydantic plugin) |
| VisionAudioForge | `services/visionaudioforge/app/` | `Lint VisionAudioForge` | flake8, 120 cols | mypy **strict** |
| Capture-agent | `agents/capture/capture_agent/` | `Lint Capture Agent` | flake8, 120 cols | mypy **strict** |
| Scripts | `scripts/` | `Lint Scripts` | flake8 **relaxed** (style) | mypy **strict** |
| Frontend | `frontend/` | `Lint Frontend` | ESLint (`next lint`) | `tsc --noEmit` **strict** |

`infra/` has no Python. `docs/` is prose.

## mypy strictness (all Python areas)

The enabled set — the same for every Python area:

| flag | what it catches |
|---|---|
| `strict_optional` (default; previously disabled via `--no-strict-optional`) | None-safety — the analog of the frontend's `strictNullChecks` |
| `warn_unused_ignores` | dead `# type: ignore` comments |
| `warn_redundant_casts` | needless `cast(...)` |
| `strict_equality` | `==`/`!=` between non-overlapping types |

`--ignore-missing-imports` is on everywhere, so uninstalled third-party libs resolve
to `Any`. That means the AST-only lint jobs (VAF, capture-agent, scripts) install
**only** flake8 + mypy — not the heavy runtime deps (torch/cv2/easyocr/websockets) —
and stay fast. The **backend** is the exception: `backend/mypy.ini` loads the
`pydantic.mypy` plugin, which requires the real deps, so that job installs
`requirements.txt`.

**Deliberately not enabled** (high-noise, low-value — the churn outweighs the safety):

- **full `--strict`** — pulls in `disallow-untyped-defs` etc., which demands annotating
  every function signature in existing code (~1900 errors on the backend alone).
- **`--warn-return-any`** — ~32 `no-any-return` errors that are mostly artifacts of
  `--ignore-missing-imports` making third-party returns `Any`; annotation purity, not
  bug-catching.

## Frontend `tsc` strictness

`frontend/tsconfig.json` `compilerOptions`:

`strict` (bundles `strictNullChecks`, `noImplicitAny`, …) plus the extra catch-more
flags: `noUnusedLocals`, `noUnusedParameters`, `noImplicitReturns`,
`noFallthroughCasesInSwitch`, `noUncheckedIndexedAccess` (every indexed access is
`T | undefined`).

**Not enabled:** `exactOptionalPropertyTypes` — for this codebase its fixes are mostly
"widen the prop type back to allow `undefined`", which neuters the flag. Low value.

## Scripts: relaxed style, strict types

`scripts/` are one-off calibration/tooling scripts, not a service, so `scripts/.flake8`
relaxes the compact-one-liner style codes — `E501` (long lines), `E701`/`E702`
(multi-statement lines), `E731` (lambda assignment) — while keeping the real-bug
pyflakes **F-codes** (unused imports/vars, undefined names, bad f-strings). **mypy runs
the full strict set** there anyway — no type relaxation.

## flake8 config

`E203` (whitespace before `:`) and `W503` (line break before binary operator) are
ignored everywhere for black compatibility. Line limit is 120 columns.

- Backend passes flags on the CLI (`--max-line-length=120 --exclude=__pycache__,migrations`).
- VAF / capture-agent / scripts each have a `.flake8` (the scripts one adds the
  compact-style relaxations above).

## Running the checks locally

From each area's directory (commands mirror CI):

```
# backend  — needs deps installed (pydantic plugin): pip install -r requirements.txt mypy flake8
flake8 app/ tests/ --max-line-length=120 --exclude=__pycache__,migrations
mypy app/ tests/                                    # reads backend/mypy.ini

# visionaudioforge  (from services/visionaudioforge/)  — flake8 + mypy only, no runtime deps
flake8 app/
mypy app/ --ignore-missing-imports --warn-unused-ignores --warn-redundant-casts --strict-equality

# capture-agent  (from agents/capture/)
flake8 capture_agent/
mypy capture_agent/ --ignore-missing-imports --warn-unused-ignores --warn-redundant-casts --strict-equality

# scripts  (from scripts/)
flake8 .
mypy . --ignore-missing-imports --warn-unused-ignores --warn-redundant-casts --strict-equality

# frontend  (from frontend/)
npx next lint
npx tsc --noEmit
```

**Gotcha (VAF/capture-agent/scripts):** to reproduce CI's mypy exactly, run it in a
venv with **only mypy** installed. A dev venv that has `cv2`/`numpy` (with their type
stubs) surfaces extra stub false-positives (e.g. `cv2.ORB_create`,
`connectedComponentsWithStats` overloads) that CI never sees, because
`--ignore-missing-imports` makes those libraries `Any` in CI.

## Conventions for fixing violations

- **Fix, don't suppress.** No new `# type: ignore` / `cast(Any, …)` / `# noqa`
  (Python) or `@ts-ignore` / `as any` (TS). If a check fires, address the real cause.
- **Provably non-None → assert (Python) / `!` (TS).** Where a value is guaranteed
  present by prior logic (an upstream guard, a just-created row, a closed-union key),
  use `assert x is not None` / `x!`. This is behavior-preserving: if the invariant ever
  breaks it fails at the same spot it would have before (AttributeError → AssertionError;
  `!` is compile-erased, so runtime is byte-identical).
- **Genuinely optional → handle it.** Add a guard / early-return / default that matches
  what the surrounding code already does (e.g. FastAPI endpoints `raise HTTPException`
  on a missing row).
- **Heterogeneous dict → annotate `dict[str, Any]`** (Python) rather than fighting the
  mixed value types — common for parse results and build-then-serialize JSON dicts.
- **Dead `# type: ignore`** flagged by `warn_unused_ignores` should be removed, not
  kept "just in case".
