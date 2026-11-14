# Coding standards

Judgement calls a reviewer checks in a diff of this fork. Mechanical rules (Python 2.7 syntax,
type hints stripped at build, formatting) are left to `./scripts/run-tests.sh` and the lint config
in `pyproject.toml`. Upstream's `CONTRIBUTING.md` is about PRs to upstream, which this fork never
sends; ignore it here.

## Upstream files

- Every edit to an upstream file is as small as it can be (usually an import plus one call into
  a `fork_*.py` module), carries a `# fork` marker, and has a row in FORK.md's `## upstream edits`
  table: what it fixes, the upstream lines touched, the fork files, and what to do on a merge
  conflict. A diff that adds, moves or removes such an edit updates that row.
- Fork code that leans on an upstream name (a method, a signature's argument order, a template
  or element id) says so in that row's "on conflict" cell, with the test that catches a rename.

## Claims in FORK.md and specs

- A claim that something is limited ("only", "never", "can't", "always 404") names a test that
  shows the limit, and that test covers each way through the code, not one case of it. Example:
  "grants are HTTP and WebDAV only" needs the FTP login, the FTP/SFTP listing *and* a full path
  through `vfs.get` checked, for an account with and without a volume of its own.
- Each FORK.md feature section ends its `known gaps:` list with bullets in the form: what
  happens, why it's kept, then the test name in parentheses with no closing full stop.
- A ticket's `## Comments` records what was found when it differs from what the ticket expected,
  and FORK.md and the spec are changed to match it in the same diff.

## Tests

- Fork tests live in `tests/test_fork_*.py` and build servers through the helpers already in that
  file (`cinit`, `reload`, `req`, ...), in the style of `tests/test_shr.py`.
- A test that repeats a protocol server's lookup instead of starting the server names the
  file and function it copies, so a change there is traceable to the test.
- Test notes are `#` comments, not docstrings. A test whose name doesn't say what it shows, or
  that pins a known limit, opens with one (naming the ticket for a known limit).
