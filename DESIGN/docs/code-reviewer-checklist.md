# Code reviewer — improvement checklist (FileTugger)

Use this when reviewing or refactoring `api/`, `web/`, and shared code. Aligns with `code-reviewer.md`.

## Security and correctness

- [ ] No critical security issues in changed paths (injection, unsafe deserialization, path traversal).
- [ ] User-controlled input validated at boundaries (URLs, tags, paths, query/body fields).
- [ ] Errors handled without leaking secrets or stack traces to clients in production.
- [ ] Resource cleanup (files, subprocesses, connections) on success and failure paths.

## Quality and maintainability

- [ ] Logic matches intended behaviour; edge cases considered (empty lists, missing fields, timeouts).
- [ ] Naming matches existing conventions in the touched module.
- [ ] No unnecessary duplication; shared behaviour lives in one place (`api/` helpers, `web/src/lib/`).
- [ ] Cyclomatic complexity stays reasonable; deeply nested code split or simplified.
- [ ] SOLID / cohesion: modules have a clear single responsibility.

## Tests

- [ ] New or changed behaviour covered by unit or integration tests (`api/tests/`, `web/src/**/*.test.*`).
- [ ] Regression tests added when fixing bugs.
- [ ] Tests are isolated (mocks/fixtures) and deterministic.

## Performance (light touch)

- [ ] No obvious hot-path regressions (tight loops on large lists, repeated I/O without need).
- [ ] Async/concurrency use is correct (no races where the domain requires ordering).

## Documentation

- [ ] Public APIs or non-obvious invariants documented briefly where maintainers need them.
- [ ] README or operator docs updated if behaviour or configuration changed.

## Dependencies and tooling

- [ ] New dependencies justified; versions pinned or constrained per project norms.
- [ ] Lint/format/typecheck clean for touched files.

## CI and review process

- [ ] CI workflow (`.github/workflows`) still passes for the change set.
- [ ] Review addresses security first, then correctness, then style.
