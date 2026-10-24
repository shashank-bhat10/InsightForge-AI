# Reliability review

## Baseline

The review started on `main` at `5fcb175`. The remote matched the requested repository. The only pre-existing untracked item was `InsightForge-review.zip`, which was preserved and excluded from Git. Root README and the five existing docs files were empty, so there were no substantive README claims to validate. The UI did label deterministic statistical summaries as AI-generated; this was corrected.

## Verified issues and fixes

| Finding | Change |
| --- | --- |
| Missing Gemini configuration prevented import | Optional key and lazy client construction |
| Environment file depended on launch location | Deterministic legacy backend/root loading, process overrides |
| SQL echo exposed query parameters in logs | Disabled echo, enabled pool pre-ping |
| Local JWT key was shorter than the recommended signing-key length | Generated a new untracked local key and enforce at least 32 characters in settings; users must sign in again |
| Duplicate database dependencies | Shared request dependency for auth and data routes |
| Unused alternate JWT implementation had a hardcoded key | Compatibility aliases to configured JWT functions |
| Startup created tables during import | Table initialization moved to app lifespan |
| Unbounded, unparsed uploads | Chunked byte limit, parsing checks, failure cleanup |
| XLS parsing dependency missing | Added xlrd; XLSX exercised, legacy XLS sample unverified |
| Non-finite preview values were invalid JSON | Normalize infinity to missing, serialize missing values as null |
| pandas 3 strings omitted from categorical analytics/ML | Include string dtype |
| Candidate models shared mutable preprocessing | Clone preprocessing for each pipeline |
| Tiny/rare classification splits failed opaquely | Minimum usable rows and class-support checks |
| ML row count included dropped targets | Report actual usable target rows |
| Measurements detected as dates; milliseconds parsed as seconds | Restrict numeric epochs to timestamp names, choose unit by magnitude |
| Removed pandas monthly alias and clipped negative lower bounds | Map M to ME, allow signed residual bounds |
| Fixed hosted API URL in frontend | Configurable VITE_API_URL with local default |
| All-missing statistics could crash formatting/export | Null-safe formatting |
| Charts required a column named Sales | Show grouped numeric/category pairs |
| Existing TypeScript/React lint failures | Typed ML/forecast responses, stable callbacks and dependencies |
| passlib logged a bcrypt-version traceback despite successful hashing | Use bcrypt directly, preserving the standard stored hash format |
| Python JWT dependency advisories without listed fixes | Replaced python-jose/ecdsa runtime dependency with compatible PyJWT token handling |
| npm advisories | Compatible dependency-lock updates; audit rerun |
| Docker copied ignored uploads directory and lacked DB gating | Create directory in image; health-gated database dependency |
| Requirements were duplicated/incomplete UTF-16 snapshots | UTF-8 direct runtime pins and a root include |
| Missing regression tests/documentation | API/service suite, synthetic sample, setup/API/interview/reference docs |

Input constraints were added for names, passwords, prompts, and titles. Registration handles duplicate-email integrity races. Provider error text is sanitized; processing exceptions are logged while clients receive generic failures. Failed AI calls no longer leave newly created empty conversations.

## Remaining constraints

The architecture was retained. No working feature was intentionally removed. The unused alternate JWT module retains its public function names through aliases. Dependency snapshots were narrowed to imports actually used; no application module imports OpenAI, Alembic, or the removed redundant direct packages.

Cross-validation, final test-set isolation, fitted feature selection, resource limits beyond upload bytes, full browser automation, live provider verification and container execution remain future work or verification limits. See the README and interview guide for details. No performance or deployment guarantee is implied.
