# Changelog Guidelines

A short, practical guide for maintaining the repository changelog. Use this to keep release notes clear, consistent, and useful for developers, QA, and stakeholders.

Why a changelog?
- Gives users and teammates a readable history of changes.
- Helps QA understand what to test for each release.
- Makes release notes / communications easier.

Recommended file
- Keep a single `CHANGELOG.md` at the repository root.
- This file documents past releases and contains an `Unreleased` section for in-progress changes.
- This document (CHANGELOG_GUIDELINES.md) explains how to update `CHANGELOG.md`.

Style & format (Keep a Changelog — simplified)
- Use sections per release with headings: `## [Unreleased]` and `## [vX.Y.Z] - YYYY-MM-DD`
- Group entries by type: Added, Changed, Fixed, Deprecated, Removed, Security.
- Use short, imperative sentences. Mention user-facing impact and any migration steps.

Minimal example
```markdown
# Changelog

## [Unreleased]
### Added
- Add `--fail-on-empty-list` CLI option for strict preflight behavior.

### Fixed
- Fix customer creation fixture race in CI.

## [1.4.8] - 2026-01-15
### Added
- Add `ENABLE_STRUCTURED_LOGS` to control per-team JSONL logging.
### Fixed
- Improve request retry/backoff in RequestUtility.
```

What to write for each entry
- Keep it short (one line) and specific.
- Mention area/component (e.g., RequestUtility, CustomersHelper, CI).
- If behavior changed for users or CI, include one-line instructions or a link to the PR for details.

Entry examples (concrete)
- Good:
  - `Added: ` Add `--fail-on-empty-list` CLI flag to make preflight fail when lists are empty.`
  - `Fixed: ` Prevent DB leak in customers cleanup helpers (ensures deletion used `force=true`).`
- Avoid:
  - Vague: `Updated some things.`
  - Too long: long technical deep-dives belong in the PR body, not the changelog.

When to update the changelog
- Update `CHANGELOG.md` in the same PR that introduces user-visible or QA-impacting changes.
- For small docs or internal-only tweaks, you may skip adding entries; prefer adding if it affects tests, CI, public behavior, or developer workflow.

Who updates it
- The PR author is responsible for adding the changelog entry.
- Reviewers should check that the changelog entry exists and is accurate before merging.

Release process (recommended)
1. Developers add entries to `CHANGELOG.md` under `Unreleased`.
2. When creating a release:
   - Update the `Unreleased` header to `## [vX.Y.Z] - YYYY-MM-DD`.
   - Add a new empty `## [Unreleased]` section at the top if future changes are expected.
   - Tag the release (GitHub release or other tooling).
3. Optionally, generate release notes from `CHANGELOG.md` when creating the GitHub release.

Versioning recommendations
- Follow semantic versioning (semver.org):
  - MAJOR for backwards-incompatible changes
  - MINOR for new backwards-compatible features
  - PATCH for backwards-compatible bug fixes
- Use the changelog groups to decide bump type:
  - Added → MINOR
  - Fixed → PATCH
  - Breaking changes (explain clearly) → MAJOR

Automating & tooling (optional)
- If you prefer automation, consider:
  - Release Drafter or GitHub Actions to draft release notes from PRs (requires consistent PR labels).
  - towncrier or git-chglog to generate or enforce changelog fragments.
- If using automation, enforce a label / PR template rule so entries are capturable.

PR checklist (changelog-related)
- [ ] Add or update changelog entry under `Unreleased` (one-liner).
- [ ] Use one of the standard groups: Added, Changed, Fixed, Deprecated, Removed, Security.
- [ ] If change is breaking, explicitly note migration steps under the entry.
- [ ] Ensure the entry is present before merging.

Tips for maintainers
- Keep entries short and consistent.
- Link to PRs when the change needs more context:
  - `Fixed: Avoid race in cleanup (see #123)`
- Periodically prune or rewrite very old verbose entries when they clutter the top-level overview (keep history).
- Consider keeping a small “migration notes” section for larger refactors.

Template snippet to copy into `CHANGELOG.md`
```markdown
## [Unreleased]
### Added
-

### Changed
-

### Fixed
-
```

If you want, I can:
- Generate an initial `CHANGELOG.md` seeded with recent notable PRs from your repo (I’ll need a list or access), or
- Add a short GitHub Actions workflow that enforces the presence of a changelog entry for PRs that modify code (by checking `CHANGELOG.md` touched when certain paths change).

Which would you like next?
