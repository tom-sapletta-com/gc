# Ticket 003: Adopt governance and repair publish strategies

- **ID**: ticket-003
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-12

## Goal and scope

Adopt the immutable `wellmanifest/new-project` v0.16.2 governance package and
repair the publish commands corrupted by the historical Goal PY013 autofix.

The implementation is limited to the standard-managed adoption payload,
ticket evidence, and `goal.yaml`. Application source, tests, package metadata,
the generated analysis under `project/`, and the target-owned `project.sh`
must remain unchanged.

## Acceptance criteria

- [x] AC-01: The adoption lock identifies published commit
  `63a03d0c2ec417f8eab9a6edb3c4ed654937a1ac` and version `0.16.2`.
- [x] AC-02: Existing `project.sh` remains byte-identical and is not listed as
  a managed adoption file.
- [x] AC-03: Python publishing uses `twine upload --skip-existing`, Node uses
  `npm publish`, and Rust uses `cargo publish`.
- [x] AC-04: Goal delivery defaults to `pull-request`, requires `goal -a`, and
  permits release modes only after trusted merge.
- [x] AC-05: The deterministic governance gate passes with zero errors.
- [x] AC-06: Existing Python tests, Ruff and Black pass without changing
  application source or tests; current mypy output is byte-for-byte equivalent
  after path normalization to the `origin/main` baseline.
- [ ] AC-07: Delivery uses a ticket-bound PR and an independent current-head
  approval before merge.
- [x] AC-08: User changes in the primary checkout are not included.

## Risks and controls

- A governance retrofit touches many managed files. Their hashes and source
  revision are controlled by `.governance/manifest.lock.json`.
- The old PY013 fix changed all publisher types. Tests inspect the three YAML
  values structurally, not by a broad text replacement.
- The primary checkout is dirty. Work happens in this dedicated worktree from
  `origin/main`; no shared index is mutated.
- The v0.16.2 package installs a governance workflow under `.github`, while
  its default manifest assigns all `.github/**` paths to infrastructure. The
  local target manifest assigns this exact managed workflow to governance;
  the upstream ownership mismatch remains a standard finding to report.
- The bounded budget is four local files outside ticket evidence. This is the
  validator's measured minimum for this atomic adoption: target manifest,
  adoption lock, optional Windows seed, and `goal.yaml`.
- Session execution authorization comes from the user's request to continue.
  It is not trusted merge approval.

## Known baseline limitation

The current dependency set resolves a mypy release that no longer supports the
configured Python 3.9 target and reports the existing `ChoicesCompleter`
annotation in `glon/cli.py`. The exact same two diagnostics occur on
`origin/main`; ticket-003 neither fixes nor suppresses them. They require a
separate application/integration ticket because both `glon/**` and
`pyproject.toml` are forbidden here.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)
