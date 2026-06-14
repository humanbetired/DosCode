# Security Standards — ReviewAgent Team

## Critical Security Rules (must fix before merge)

### S1 — No Hardcoded Secrets
Any credential found in source code is an automatic PR rejection.
This includes: passwords, API keys, tokens, connection strings.
Fix: use os.environ.get('SECRET_NAME') or python-dotenv.

### S2 — Dangerous Function Usage
Functions that must never be used with external input:
- eval(), exec() — arbitrary code execution risk
- pickle.loads() — deserialization attack risk
- subprocess with shell=True — command injection risk
Fix: use ast.literal_eval() for safe evaluation, avoid pickle for untrusted data.

### S3 — Input Validation
All data from external sources (API, user input, files) must be validated.
Use pydantic models or explicit type checks before processing.

### S4 — Dependency Security
Run pip audit regularly.
Pin dependency versions in requirements.txt.
Never use packages with known critical CVEs.

## Severity Levels
- CRITICAL: hardcoded secrets, eval with user input → block merge immediately
- HIGH: missing input validation, shell=True → must fix before merge  
- MEDIUM: deprecated functions, weak crypto → fix in current sprint
- LOW: code style, minor improvements → fix when convenient