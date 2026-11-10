# Security Defect Investigation

Report a security finding as **Confirmed** only when there is a concrete path from attacker-controlled input to a dangerous sink. Otherwise call it a **Potential risk** and name the missing link (for example, "exploitable only if `name` comes from user input; caller not shown").

Do not assign CVE identifiers, CVSS scores, or claim exploitation unless the user provided them or you verified them.

## Contents
- Method: source, propagation, sink
- Injection
- Authentication and authorization
- Secrets and sensitive data
- Memory safety
- Deserialization and file handling
- Reporting security findings

## Method: source, propagation, sink

1. **Source**: where does untrusted data enter? (HTTP params, headers, cookies, file uploads, message queues, environment set by users, database fields written by users)
2. **Propagation**: follow the value through assignments, function calls, and storage. Note any validation or encoding and whether it fits the sink.
3. **Sink**: where would malicious data cause harm? (SQL/NoSQL query, shell command, HTML output, file path, deserializer, redirect URL, template engine, `eval`)
4. **Verdict**: the fix belongs at the sink (parameterize, encode, allow-list) and, where appropriate, at the source (validate).

## Injection

| Sink | Unsafe pattern | Fix |
|---|---|---|
| SQL | String concatenation or f-strings into a query | Bound parameters (`?`, `%s`, `$1`, `:name`) via the driver; allow-list identifiers that cannot be parameterized (column/table names, sort order) |
| Shell | `os.system`, `subprocess(..., shell=True)`, `exec`, backticks with user input | Pass an argument list without a shell; allow-list values |
| HTML | Unescaped interpolation, `innerHTML`, `dangerouslySetInnerHTML`, `|safe`, `raw` | Context-aware auto-escaping; sanitize with a maintained library when HTML is required |
| Path | `open(base + user_path)` | Resolve the real path and verify it stays under the allowed base directory |
| Redirect | `redirect(request.args['next'])` | Allow-list hosts or accept only relative paths |
| Template | Rendering user input as a template | Pass user data as variables, never as template source |
| LDAP / XPath / NoSQL | Building filters by concatenation | Driver-provided escaping or query builders; reject operator keys (`$where`, `$ne`) from user JSON |

## Authentication and authorization

- Missing authorization check on an endpoint or object (IDOR): verify the current user owns or may access the requested ID.
- Authorization done only in the UI/client.
- Comparing secrets with `==` (timing leak) — use constant-time comparison.
- JWT: accepting `alg: none`, not verifying signature or expiry, using a weak shared secret.
- Session fixation: session ID not rotated on login.
- Password storage without a slow, salted hash (bcrypt, scrypt, Argon2).

## Secrets and sensitive data

- Hard-coded credentials, API keys, or private keys in source. Recommend rotation, not just removal — the secret is already in history.
- Secrets or personal data written to logs, error messages, or analytics.
- Verbose error pages or stack traces returned to clients in production.
- TLS verification disabled (`verify=False`, `rejectUnauthorized: false`, `InsecureSkipVerify: true`).

## Memory safety

For C, C++, and `unsafe` Rust: buffer overflows, use-after-free, double free, integer overflow feeding an allocation size, format string bugs. Recommend AddressSanitizer/UBSan or fuzzing to confirm; do not claim exploitability without evidence.

## Deserialization and file handling

- Unsafe deserializers on untrusted data: Python `pickle`, `yaml.load` without `SafeLoader`, Java native serialization, PHP `unserialize`, .NET `BinaryFormatter`.
- Archive extraction without path checks (zip slip).
- Uploads stored under a web-served directory or trusted by extension/MIME type alone.
- XML parsers with external entities enabled (XXE).

## Reporting security findings

For each finding include: location, source → sink path, status (Confirmed / Potential risk), severity, a minimal fix, and a safe way to test it (a unit test with a malicious payload, not an attack on a live system). Never run exploits against systems the user has not explicitly authorized.
