# Ticket preprompt

- **Task ID**: ticket-003
- **Task title**: Adopt governance and repair publish strategies
- **Created**: 2026-08-12T19:06:11Z

Keep executable implementation outside this governance/evidence directory.
Read a human-owned user-*.md file only when one exists.
The request to execute this work creates SESSION_EXECUTION_AUTHORIZATION;
proceed within the recorded intent without a redundant confirmation prompt.
Require new authority for destructive action, secrets, external coordination,
material objective expansion and trusted merge approval.

## Technical directives

- Standard source: `wellmanifest/new-project` v0.16.2 at immutable commit
  `63a03d0c2ec417f8eab9a6edb3c4ed654937a1ac`.
- Delivery runtime: public Goal 2.1.300, imported outside its source checkout.
- Preserve the target-owned root `project.sh` byte-for-byte.
- Treat `.governance/manifest.lock.json` as the managed-file hash source.
- Do not edit application source, tests, generated code-analysis artifacts,
  package version, or human participant files.
- Publish implementation only through a ticket-bound pull request.
