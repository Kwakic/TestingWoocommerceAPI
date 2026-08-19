# 🤖 GitHub Production Branch Protection & CI Quality Gates

A practical guide for configuring a GitHub repository so that the
default branch (`main`) is protected, pull requests are validated by CI,
and failed tests cannot be merged accidentally.

This guide is written for developers, QA engineers, SDETs, and juniors
who may already know similar concepts from GitLab, Bitbucket, Jenkins,
or another CI/CD platform but are new to GitHub Actions.

> **Project context:** This guide reflects the CI architecture used by
> this project: separate Preflight, Smoke, Contract, Integration,
> Regression, Performance, and Security workflows, with entity-based
> test matrices where appropriate.

------------------------------------------------------------------------

## 1. 🎯 The Goal

A production-style repository should make this workflow difficult to
bypass accidentally:

``` text
Developer
   │
   │  create feature branch
   ▼
feature/my-change
   │
   │  push
   ▼
GitHub Pull Request → main
   │
   ├── Preflight
   ├── Smoke
   ├── Contract
   └── Integration
          │
          ▼
     Quality Gates
          │
     ┌────┴────┐
     │         │
    FAIL      PASS
     │         │
     ▼         ▼
  Block PR   Merge
```

The important distinction is:

-   **CI workflow** = performs the tests.
-   **Quality Gate** = gives GitHub one stable result representing that
    suite.
-   **Required status check** = tells GitHub that the Quality Gate must
    pass before `main` can be merged.

These are three different concepts.

------------------------------------------------------------------------

# 2. 🆚 GitHub Terminology vs Other CI Platforms

If you already know GitLab, Bitbucket, or Jenkins, the concepts are
familiar even though the names differ.

| Concept | GitHub | GitLab | Jenkins / Bitbucket equivalent |
|---|---|---|---|
| CI pipeline definition | GitHub Actions workflow | `.gitlab-ci.yml` pipeline | Jenkinsfile / Bitbucket Pipelines |
| CI execution unit | Job | Job | Stage / step |
| CI configuration | `.github/workflows/*.yml` | `.gitlab-ci.yml` | Jenkinsfile / `bitbucket-pipelines.yml` |
| Pull request | Pull Request | Merge Request | PR / Pull Request |
| Protected default branch | Branch protection / Ruleset | Protected branch | Branch permissions |
| CI result used to block merge | Required status check | Required pipeline/check | Build status / merge check |
| Quality Gate | A job such as `Smoke Quality Gate` | Job/check used as gate | Quality gate / build gate |
| Matrix execution | Matrix strategy | Parallel/matrix-style jobs | Parallel stages |
| Scheduled CI | `schedule` | `schedule` | Jenkins cron |
| Manual CI | `workflow_dispatch` | Manual job/pipeline | Build manually |
| Reusable CI | Reusable workflow | Includes/templates | Shared libraries |

The underlying principle is the same:

> **Code should not enter the protected branch until the repository's
> required quality conditions are satisfied.**

------------------------------------------------------------------------

# 3.🛡️️ GitHub's Two Protection Mechanisms

GitHub currently provides two related approaches:

1.  **Branch protection rules**
2.  **Repository rulesets**

For a new production repository, **Rulesets are the preferred modern
approach** because they can be layered and have explicit Active/Disabled
enforcement states.

Classic branch protection rules are still valid and widely used. This
project currently uses that interface, so the settings below describe it
first.

* GitHub documentation: - Branch protection:
https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches -

* Rulesets:
https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets

------------------------------------------------------------------------

# 4. ⚔️ Protect `main`

Navigate to:

``` text
Repository
  → Settings
  → Branches
  → Branch protection rules
```

or, for the newer approach:

``` text
Repository
  → Settings
  → Rules
  → Rulesets
```

Target:

``` text
main
```

The default branch should normally be protected.

------------------------------------------------------------------------

# 5. ⭐ Recommended Production Settings

The following is a good baseline for a professional repository.

## 5.1 Require a pull request before merging

### Recommended: YES

``` text
[x] Require a pull request before merging
```

This prevents normal direct changes from entering `main`.

The normal flow becomes:

``` text
feature/my-change
       │
       ▼
      PR
       │
       ▼
     main
```

This is one of the most important protections.

### Why?

Without it, someone can accidentally do:

``` bash
git switch main
git commit
git push origin main
```

and bypass the normal review/CI workflow.

------------------------------------------------------------------------

# 6. 🔎 Pull Request Reviews

## I. Require approvals

### Production team: YES

A common starting point is:

``` text
[x] Require approvals
Required approvals: 1
```

This means another person must review the PR before it can be merged.

### Solo portfolio repository

If you are the only person maintaining the repository, requiring one
approval can create an artificial deadlock:

``` text
You open PR
   ↓
CI passes
   ↓
GitHub says: "1 approval required"
   ↓
Nobody else exists to approve it
```

For a personal portfolio project, it is reasonable to leave this
disabled.

For a team repository, require at least one approval.

------------------------------------------------------------------------

## II. Dismiss stale approvals

### Recommended: YES for team repositories

``` text
[x] Dismiss stale pull request approvals when new commits are pushed
```

Why?

Suppose:

``` text
Developer pushes code
        ↓
Reviewer approves
        ↓
Developer pushes another commit
        ↓
The code has changed
```

The old approval should generally not be treated as approval of the new
code.

------------------------------------------------------------------------

## III. Require review from Code Owners

### Recommended: YES when the repository has multiple owners

Use a `CODEOWNERS` file when different teams own different parts of the
repository.

For a small personal project:

``` text
[ ] Require review from Code Owners
```

is perfectly reasonable.

------------------------------------------------------------------------

## IV. Require approval of the most recent reviewable push

### Recommended: YES for stronger team governance

This ensures the latest changes are reviewed by somebody other than the
person who pushed them.

For a solo portfolio project, this can again become unnecessarily
restrictive.

------------------------------------------------------------------------

# 7.📌 Required Status Checks

This is where CI becomes an actual merge gate.

Enable:

``` text
[x] Require status checks to pass before merging
```

GitHub then allows you to select individual status checks.

The key point is:

> **Do not select every individual test job.**

Instead, create stable **Quality Gate** jobs and make those required.

------------------------------------------------------------------------

# 8.💡 Why Quality Gates Are Useful

Imagine Smoke uses a matrix:

``` text
Smoke Tests
├── Test • customers
├── Test • orders
├── Test • products
└── Test • coupons
```

If you make all four jobs required, your GitHub branch protection
becomes coupled to the current entity list.

Tomorrow you add:

``` text
Test • subscriptions
```

Now the protection configuration may need to change.

Instead, create:

``` text
Smoke Quality Gate
```

which depends on all Smoke test jobs.

Conceptually:

``` text
Smoke Tests
├── customers ──┐
├── orders ─────┤
├── products ───┤
└── coupons ────┤
                ▼
        Smoke Quality Gate
```

GitHub only needs to know about:

``` text
Smoke Quality Gate
```

This is a much more stable interface between your CI implementation and
your repository protection.

------------------------------------------------------------------------

# 9. ⛩️ The Quality Gate Pattern

A Quality Gate is simply a GitHub Actions job that aggregates the result
of another job or group of jobs.

Example:

``` yaml
smoke-gate:

  name: Smoke Quality Gate

  needs:
    - test

  if: always()

  runs-on: ubuntu-latest

  steps:

    - name: Validate smoke results
      run: |
        if [ "${{ needs.test.result }}" != "success" ]; then
          echo "Smoke tests failed."
          exit 1
        fi

        echo "Smoke tests passed."
```

The important parts are:

### `needs`

``` yaml
needs:
  - test
```

The gate waits for the test job.

### `if: always()`

``` yaml
if: always()
```

This allows the gate itself to run even when the test job fails.

That is important because we want:

``` text
Tests fail
   ↓
Quality Gate runs
   ↓
Quality Gate fails
```

rather than:

``` text
Tests fail
   ↓
Quality Gate is skipped
```

A skipped gate is much less useful as a required status check.

------------------------------------------------------------------------

# 10.🎯 One Quality Gate Per Protected Suite

A good structure for this project is:

``` text
Preflight
   └── Preflight Quality Gate       (optional)

Smoke
   ├── entity tests
   └── Smoke Quality Gate           (recommended)

Contract
   ├── REST/GraphQL contract tests
   └── Contract Quality Gate        (recommended)

Integration
   ├── entity tests
   └── Integration Quality Gate     (recommended)
```

The Quality Gate is deliberately independent from whether GitHub
requires it.

That gives you an important choice:

``` text
Workflow contains Quality Gate
              │
              ├── Required status check
              │       → blocks merge
              │
              └── Not required
                      → informational only
```

This is why it is useful to keep the Quality Gate in the workflow even
when you are still experimenting.

------------------------------------------------------------------------

# 11.🔥 Recommended Required Checks for This Project

Once the workflows are stable, a strong PR configuration is:

``` text
[x] Require status checks to pass before merging

Required:

    ✓ Preflight Quality Gate
    ✓ Smoke Quality Gate
    ✓ Contract Quality Gate
    ✓ Integration Quality Gate
```

However, these do not all have to become required immediately.

A sensible rollout is:

### Phase 1 --- Experiment

``` text
Integration Quality Gate    required
Smoke Quality Gate          optional
Contract Quality Gate       optional
Preflight                   optional
```

Verify that the gates correctly turn red when tests fail.

### Phase 2 --- Production

``` text
Integration Quality Gate    required
Smoke Quality Gate          required
Contract Quality Gate       required
Preflight Quality Gate      required (if useful and stable)
```

This is exactly why keeping the Quality Gate code in the workflows is
useful: the GitHub protection setting can be changed independently.

------------------------------------------------------------------------

# 12.⚠️ Important: Select the Job Name, Not the Workflow Name

This causes a lot of confusion for newcomers.

Suppose the workflow says:

``` yaml
name: Integration Tests
```

and the job says:

``` yaml
integration-gate:

  name: Integration Quality Gate
```

GitHub may display:

``` text
Integration Tests / Integration Quality Gate
```

The important status check is the **job/check name**:

``` text
Integration Quality Gate
```

not the workflow title:

``` text
Integration Tests
```

For reusable workflows, GitHub may display a hierarchical name such as:

``` text
Integration Tests / Test • products
```

GitHub's status-check documentation describes the naming behavior for
normal and reusable workflow jobs.

**Best practice:**

Use stable, unique job names for checks that will become required.

------------------------------------------------------------------------

# 13.🌿 Require Branches to Be Up to Date

GitHub provides:

``` text
[x] Require branches to be up to date before merging
```

This is the stricter status-check mode.

Example:

``` text
main
 │
 ├── commit A
 └── commit B

feature branch
 └── based on A
```

Someone merges another PR:

``` text
main
 │
 ├── A
 ├── B
 └── C
```

Your feature branch is now behind `main`.

With the strict setting enabled, you may need to update your branch and
run CI again before merging.

### Production recommendation

``` text
[x] Require branches to be up to date before merging
```

This gives stronger confidence that the tested code includes the latest
`main`.

### Trade-off

It can cause more CI runs.

For a busy repository, teams may consider a merge queue or a less strict
configuration.

For a small QA/SDET portfolio project, the strict option is perfectly
reasonable.

------------------------------------------------------------------------

# 14.💬 Require Conversation Resolution

### Recommended: YES

``` text
[x] Require conversation resolution before merging
```

This means review conversations must be resolved before the PR can
merge.

Example:

``` text
Reviewer:
"This test should use the shared fixture."

Developer:
"Fixed."

→ conversation resolved
```

It prevents review comments from silently remaining unresolved.

------------------------------------------------------------------------

# 15. Signed Commits

``` text
[ ] Require signed commits
```

### Recommendation for a small project

Optional.

Signed commits are valuable in security-sensitive or highly governed
environments, but they introduce additional setup for contributors.

Consider enabling them when the project requires strong commit
provenance.

------------------------------------------------------------------------

# 16. Linear History

``` text
[ ] Require linear history
```

This is a style and history-management decision.

If your repository consistently uses:

``` text
Squash and merge
```

you may not need this protection.

For many application repositories, a clean history is useful, but this
should not be enabled simply because it sounds "more professional."

Choose a merge strategy first, then decide whether linear history is
needed.

------------------------------------------------------------------------

# 17. Force Pushes

### Production recommendation: NO

Do not enable:

``` text
[ ] Allow force pushes
```

For a protected `main`, force pushes should normally be blocked.

You don't want:

``` bash
git push --force origin main
```

rewriting the shared production history.

------------------------------------------------------------------------

# 18. Branch Deletion

### Production recommendation: NO

Do not enable:

``` text
[ ] Allow deletions
```

`main` should remain available.

Feature branches can safely be deleted after their PRs are merged.

------------------------------------------------------------------------

# 19. Bypass Protection

GitHub provides:

``` text
[x] Do not allow bypassing the above settings
```

This is a strong protection.

### Team / production repository

Recommended:

``` text
[x] Do not allow bypassing the above settings
```

This means administrators are also subject to the protection.

### Personal portfolio repository

Think carefully before enabling it.

As you discovered during setup, you can accidentally lock yourself into
a situation where:

``` text
PR
 ↓
CI passes
 ↓
GitHub requires approval
 ↓
You are the only maintainer
 ↓
Cannot merge
```

The setting is not broken. It is doing exactly what you asked.

------------------------------------------------------------------------

# 20. Deployment Protection

If your repository deploys to an actual environment, GitHub can also
require:

``` text
Require deployments to succeed before merging
```

For example:

``` text
PR
 ↓
CI
 ↓
Deploy to staging
 ↓
Staging validation
 ↓
Merge
```

For this project, this is currently unnecessary because the repository
is primarily a test framework and CI validation project.

Use it when an actual deployment environment becomes part of the release
process.

------------------------------------------------------------------------

# 21. Merge Queue

For a busy team repository, consider:

``` text
Require merge queue
```

A merge queue is useful when many PRs are being merged concurrently and
you want GitHub to validate changes in an orderly queue.

For a small personal repository:

``` text
Not necessary
```

------------------------------------------------------------------------

# 22. Recommended Production Configuration

For a typical professional team repository:

``` text
Branch:
    main

Pull requests:
    [x] Require a pull request before merging
    [x] Require approvals
        → 1 approval
    [x] Dismiss stale approvals
    [ ] Code Owners
        → YES when the team uses CODEOWNERS
    [x] Require conversation resolution

CI:
    [x] Require status checks to pass
    [x] Require branches to be up to date

Required checks:
    ✓ Preflight Quality Gate
    ✓ Smoke Quality Gate
    ✓ Contract Quality Gate
    ✓ Integration Quality Gate

History/security:
    [ ] Require signed commits
        → optional
    [ ] Require linear history
        → depends on merge strategy

Branch safety:
    [ ] Allow force pushes
    [ ] Allow deletions

Administration:
    [x] Do not allow bypassing
        → recommended for team repositories

Deployment:
    [ ] Require deployments
        → enable when real deployment environments exist

Merge queue:
    [ ] Require merge queue
        → enable for busy repositories
```

------------------------------------------------------------------------

# 23. Recommended Configuration for a Personal QA/SDET Portfolio

A portfolio repository has a slightly different goal.

You want to demonstrate professional practice without creating
unnecessary administrative friction.

Recommended:

``` text
[x] Require pull request before merging

[ ] Require approvals
    → unless another reviewer is available

[x] Require status checks

Required:
    ✓ Smoke Quality Gate
    ✓ Contract Quality Gate
    ✓ Integration Quality Gate

[x] Require branches to be up to date

[x] Require conversation resolution

[ ] Require signed commits
    → optional

[ ] Require linear history
    → optional

[ ] Allow force pushes

[ ] Allow deletions

[ ] Do not allow bypassing
    → consider carefully on a solo repository
```

This gives you a very strong portfolio story:

> "The default branch is protected. Changes are made through pull
> requests, CI executes the appropriate test suites, and required
> quality gates prevent failed changes from being merged."

------------------------------------------------------------------------

# 24. Why You Should Not Require Every Matrix Job

Suppose you currently have:

``` text
Smoke Tests
├── customers
├── orders
├── products
└── coupons
```

It is tempting to add all four to branch protection.

Avoid doing that.

Instead:

``` text
Smoke Tests
├── customers ──┐
├── orders ─────┤
├── products ───┤
└── coupons ────┤
                ▼
        Smoke Quality Gate
```

Then branch protection only knows:

``` text
Smoke Quality Gate
```

This is more maintainable.

If you later add:

``` text
subscriptions
refunds
payments
```

the protection rule does not need to change.

The workflow changes; the external contract stays stable.

------------------------------------------------------------------------

# 25. Why Quality Gates Should Be in the Workflow Even If They Are Not Required

This is an important design choice.

You can have:

``` yaml
smoke-gate:
  name: Smoke Quality Gate
```

without immediately making it a required GitHub status check.

That gives you:

``` text
                    Workflow
                       │
             ┌─────────┴─────────┐
             │                   │
       Quality Gate         GitHub rule
             │                   │
       always available      optional
             │                   │
             └─────────┬─────────┘
                       │
                later → required
```

This is useful when introducing CI protection gradually.

You can:

1.  Add the Quality Gate.
2.  Push a PR.
3.  Intentionally break a test.
4.  Verify the gate fails.
5.  Fix the test.
6.  Verify the gate passes.
7.  Add the gate to required status checks.

This separates **testing the CI implementation** from **changing
repository governance**.

------------------------------------------------------------------------

# 26. What Happens When a Test Fails?

Correct behavior:

``` text
Test job
   │
   ▼
❌ Test fails
   │
   ▼
Quality Gate runs
   │
   ▼
❌ Quality Gate fails
   │
   ▼
GitHub PR
   │
   ▼
🚫 Merge blocked
```

The workflow should still collect diagnostics.

For example:

``` yaml
- name: Upload artifacts
  if: always()
  uses: actions/upload-artifact@v4
```

Do not hide test failures with:

``` yaml
continue-on-error: true
```

unless you have a very deliberate reason.

The desired behavior is:

``` text
Tests fail
   ↓
Artifacts still collected
   ↓
Report still generated when appropriate
   ↓
Workflow remains FAILED
   ↓
Quality Gate remains FAILED
   ↓
PR remains BLOCKED
```

Failure visibility is more important than making the CI page look green.

------------------------------------------------------------------------

# 27. Status Check Naming Is Part of Your CI Design

Treat required check names as an API.

Bad:

``` text
test
build
run
```

Better:

``` text
Smoke Quality Gate
Contract Quality Gate
Integration Quality Gate
```

These names communicate exactly what the check means.

They also create a stable interface between:

``` text
GitHub Actions implementation
             ↓
       Quality Gate
             ↓
    GitHub repository rules
```

Do not casually rename a required Quality Gate without updating the
repository rule.

------------------------------------------------------------------------

# 28. Keep CI Workflow Names and Quality Gate Names Different

For example:

``` yaml
name: Smoke Tests 🔥
```

and:

``` yaml
smoke-gate:
  name: Smoke Quality Gate
```

This gives GitHub a clear hierarchy:

``` text
Smoke Tests 🔥
    ├── Discover framework entities
    ├── Test • customers
    ├── Test • orders
    ├── Test • products
    ├── Test • coupons
    └── Smoke Quality Gate
```

The workflow describes **what is running**.

The Quality Gate describes **what must be true before merging**.

------------------------------------------------------------------------

# 29. PR CI vs Post-Merge CI

Do not confuse these two purposes.

## Pull request

``` text
PR → main

Preflight
Smoke
Contract
Integration

        ↓

Can this change safely enter main?
```

## After merge

``` text
main

Smoke
Regression
Performance
Security
```

These answer different questions.

PR:

> "Should this change be allowed into main?"

Post-merge:

> "Is the current main branch healthy?"

------------------------------------------------------------------------

# 30. Heavy Tests Should Not Automatically Become PR Gates

For this project:

``` text
Required PR gates

Preflight       Fast
Smoke           Critical business paths
Contract        API compatibility
Integration     API + DB consistency
```

While:

``` text
Regression      Nightly
Performance     Weekly
Security        Scheduled
```

This keeps PR feedback useful instead of turning every pull request into
a 60-minute pipeline.

Your project documentation already follows this segmentation philosophy.
fileciteturn6file0L21-L30

------------------------------------------------------------------------

# 31. A Practical GitHub Settings Checklist

Before calling `main` production-protected, verify:

``` text
MAIN BRANCH
────────────────────────────────────────

[x] Pull request required
[x] Status checks required
[x] Conversation resolution
[x] Branch up-to-date requirement

REVIEWS
────────────────────────────────────────

[ ] Approval required for solo repository
[x] 1 approval for team repository
[x] Dismiss stale approvals for team repository

QUALITY GATES
────────────────────────────────────────

[ ] Preflight Quality Gate
[ ] Smoke Quality Gate
[ ] Contract Quality Gate
[ ] Integration Quality Gate

SAFETY
────────────────────────────────────────

[ ] Force pushes
[ ] Branch deletion

OPTIONAL SECURITY
────────────────────────────────────────

[ ] Signed commits
[ ] CODEOWNERS
[ ] Deployment protection
[ ] Merge queue

ADMINISTRATIVE
────────────────────────────────────────

[x] No bypass
    → team/production repository
```

------------------------------------------------------------------------

# 32. The Golden Rule

The most important principle is:

> **Protect `main`, but do not make the protection dependent on the
> internal implementation of your CI.**

Therefore:

``` text
                    GitHub
                       │
                Required checks
                       │
                       ▼
              Quality Gate
                       │
                       ▼
                CI test jobs
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       entity       entity       entity
       tests        tests        tests
```

The Quality Gate is the boundary between:

``` text
CI implementation
```

and:

``` text
repository governance
```

That is why keeping Quality Gates in the workflows---even when they are
currently optional---is a useful production practice.

------------------------------------------------------------------------

# 33. Final Recommended Setup for This Repository

For this project, the target state is:

``` text
                         Pull Request → main
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                Preflight       Smoke        Contract
                    │             │             │
                    ▼             ▼             ▼
                 Quality       Quality       Quality
                  Gate          Gate          Gate
                    │             │             │
                    └─────────────┼─────────────┘
                                  │
                             Integration
                                  │
                                  ▼
                           Quality Gate
                                  │
                                  ▼
                         Required PR checks
                                  │
                         ┌────────┴────────┐
                         ▼                 ▼
                       FAIL              PASS
                         │                 │
                         ▼                 ▼
                    Block merge       Allow merge
```

And the GitHub branch protection/ruleset should know only about the
stable gates:

``` text
Preflight Quality Gate
Smoke Quality Gate
Contract Quality Gate
Integration Quality Gate
```

not:

``` text
products
customers
orders
coupons
test
discover-entities
publish-report
```

The latter are implementation details of the CI pipeline.

------------------------------------------------------------------------

## 34. Useful GitHub Documentation

-   GitHub protected branches:
    https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches

-   GitHub rulesets:
    https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets

-   GitHub status checks:
    https://docs.github.com/en/pull-requests/reference/status-checks

-   GitHub required status-check troubleshooting:
    https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks

------------------------------------------------------------------------

**Document purpose:** Practical GitHub branch protection and CI Quality
Gate guide\
**Audience:** Developers, QA Engineers, SDETs, juniors, and engineers
migrating from other CI/CD platforms\
**Last reviewed:** 2026-08-19
