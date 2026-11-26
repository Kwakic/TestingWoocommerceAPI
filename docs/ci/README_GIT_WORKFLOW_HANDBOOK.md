# Git Workflow Handbook for QA Engineers and SDETs

A practical, beginner-friendly guide to Git, from your first branch and Pull Request (PR) to investigating regressions, hotfixes and parallel development.

**Learning path:** Start with Sections 1–5. Use Sections 6–10 when debugging or handling more complex workflows. Sections 11–14 cover team practices and optional configuration.

Examples assume Git Bash or a similar shell, a repository with `main` as its integration branch, and `origin` as its primary remote. Adapt branch names, paths, test commands and CI policies to your project. Commands containing `<placeholders>` require actual values; do not copy the angle brackets into the shell.

## Contents

1. [Git fundamentals](#1-git-fundamentals)
2. [Daily Git command reference](#2-daily-git-command-reference)
3. [Standard branch-to-PR workflow](#3-standard-branch-to-pr-workflow)
4. [Inspecting changes with diff and log](#4-inspecting-changes-with-diff-and-log)
5. [Fetch, pull, merge and rebase](#5-fetch-pull-merge-and-rebase)
6. [Stash and urgent hotfix workflow](#6-stash-and-urgent-hotfix-workflow)
7. [Working on multiple tickets with worktree](#7-working-on-multiple-tickets-with-worktree)
8. [Undoing changes and recovering work](#8-undoing-changes-and-recovering-work)
9. [Troubleshooting common Git problems](#9-troubleshooting-common-git-problems)
10. [Git for QA debugging](#10-git-for-qa-debugging)
11. [Remotes and upstream tracking](#11-remotes-and-upstream-tracking)
12. [Team workflow, CI and security](#12-team-workflow-ci-and-security)
13. [Pre-commit, line endings and aliases](#13-pre-commit-line-endings-and-aliases)
14. [PyCharm workflow and daily checklist](#14-pycharm-workflow-and-daily-checklist)

## 1. Git fundamentals

Git is a version control system. GitHub and GitLab are platforms that host Git repositories and provide PRs, reviews and CI integration.

### Where your changes live

```text
Working directory ---- git add ----> Staging area ---- git commit ----> Local repository
                                                                            |
                                                                         git push
                                                                            v
                                                                     Remote repository
```

| Term | Plain English |
| --- | --- |
| Working directory | The files you currently edit in your IDE. |
| Staging area (index) | The exact changes selected for the next commit. |
| Commit | A saved snapshot of tracked project content, identified by a hash. |
| Branch | A movable pointer to a commit; normally one branch per task. |
| HEAD | Your current checkout, normally pointing through the current branch to a commit. |
| `main` | Your local integration branch. |
| `origin` | A conventional name for a remote repository. |
| `origin/main` | Your local record of the remote `main`, updated by fetching (or certain other remote operations). |
| Upstream | The branch your local branch tracks by default. |
| Pull Request (PR) | A request to review and integrate changes into another branch; not a Git CLI operation. |

Uncommitted edits are in the working directory/index, not stored in a branch commit. Git may carry compatible edits across a branch switch or refuse the switch if it would overwrite them.

## 2. Daily Git command reference

These are the most useful commands to learn first. Run them from the repository root unless a different directory is intended.

| Command | What it does / when to use it |
| --- | --- |
| `git clone <url>` | Download a repository for the first time. |
| `git status` | Check current branch, staged, unstaged and untracked files. Start here. |
| `git branch` | List local branches. |
| `git branch -a` | List local and remote-tracking branches. |
| `git branch -r` | List remote-tracking branches only. |
| `git branch -vv` | Inspect local branches and upstream tracking. |
| `git switch main` | Switch to an existing local branch. |
| `git switch -c feature/QA-123` | Create and switch to a new branch. |
| `git switch -` | Return to your previously checked-out branch. |
| `git diff` | Inspect unstaged changes to tracked files. |
| `git add <file>` | Stage a specific file. |
| `git add -p` | Interactively stage selected changes within files. |
| `git add .` | Stage changes, including deletions and nonignored new files, under the current directory. Review before using. |
| `git diff --staged` | Review exactly what the next ordinary commit will include. |
| `git commit -m "test: add checkout coverage"` | Save staged changes locally. |
| `git fetch origin` | Download remote updates without integrating them into your current branch. |
| `git pull --ff-only` | Fetch and integrate the configured upstream only if no merge commit or rebase is needed. |
| `git push -u origin feature/QA-123` | First push; publish the branch and set upstream tracking. |
| `git push` | Publish subsequent commits to the configured destination. |
| `git log --oneline -10` | Inspect recent commits. |
| `git stash push -u -m "WIP: QA-123"` | Temporarily save tracked edits and untracked, nonignored files. |
| `git stash pop` | Restore the latest stash and remove it if successful. |
| `git branch -d feature/QA-123` | Delete a local branch subject to Git's merged-history checks. |

### Modern vs classic syntax

| Task | Recommended | Classic equivalent |
| --- | --- | --- |
| Switch branches | `git switch main` | `git checkout main` |
| Create and switch | `git switch -c fix/QA-123` | `git checkout -b fix/QA-123` |
| Discard unstaged tracked edits | `git restore -- file.py` | `git checkout -- file.py` |

The last row discards edits. Inspect them before running it. `switch` and `restore` separate the two common jobs of `checkout`.

## 3. Standard branch-to-PR workflow

**Scenario:** You are implementing automated customer API tests for ticket QA-123. Your company uses a protected `main` branch and squash-merges PRs.

### Step 1 — Start from an updated main

```bash
# If you have not cloned the repository yet:
# git clone <repository-url>
# cd <repository-directory>

git status
git switch main
git pull --ff-only origin main
```
If you see:

`There is no tracking information for the current branch`

Run once:

`git branch -u origin/main
`



Note: If the working tree is dirty, commit or stash your work on the appropriate branch first. If fast-forward-only pull refuses, stop and inspect the divergence (Section 9).

### Step 2 — Create a branch for the ticket

```bash
git switch -c test/QA-123-customer-validation
```

Do your work on this branch, not directly on `main`.

### Step 3 — Implement and validate your tests

Example commands for a Python/Pytest project:

```bash
pytest tests/customers/api -q
# If the project defines this marker:
pytest -m smoke
```

Run the specific affected tests first, then the appropriate smoke, integration or regression suite. Confirm that your environment and test data are correct.

### Step 4 — Stage and commit

```bash
git status
git diff
git add tests/customers/api/
# or to add all changes
git add .
git diff --staged
pre-commit run
# or:
pre-commit run --all-files
git commit -m "test(customers): add negative validation cases"
```
💡 If pre-commit modifies files → run `git add . `again

Stage any other intended files individually. If configured hooks modify files, inspect and stage those changes before retrying the commit (Section 13).

### Step 5 — Integrate the latest main, if needed

Stay on your test branch:

```bash
# downloads updates for all branches on GitHub, including main, merged branches, and unmerged feature or created by your teammates
git fetch origin
# show me every commit that is on origin/main that I do NOT have in my current branch yet
git log --oneline HEAD..origin/main
# or check for: "What do I have that remote doesn’t?
git log origin/main..HEAD --oneline
git merge origin/main
# or
git merge --no-edit origin/main
# The --no-edit flag skips opening the text editor for the merge commit message and automatically uses Git's default message.

```

Use merge as the beginner-friendly default: it preserves existing commits and works well for shared branches. If your team's policy requires a linear feature history, you can rebase a private branch instead (Section 5). Run relevant tests again after integration. Sync when needed; it does not guarantee that another change will not reach `main` later.

or (cleaner history):

```bash
git fetch origin
# check for possible changes made in main branch
git log HEAD..origin/main --oneline
git rebase origin/main
```

### Step 6 — Push and create a PR

```bash
git push -u origin test/QA-123-customer-validation
```

On GitHub, create a PR with **base `main`** and **compare `test/QA-123-customer-validation`**. Explain the ticket, test coverage, how you validated the change, known risks and any environment changes. Subsequent commits and `git push` update the same open PR.

The PR can be opened early as a draft. Merge only after required approvals, CI checks and team policies are satisfied. If the branch needs another sync, repeat Step 5, retest and push again.

### Step 7 — Merge and clean up

Once the PR is merged on the hosting platform:

```bash
git switch main
git pull --ff-only origin main
git branch -d test/QA-123-customer-validation
git fetch origin --prune
```

Delete the remote feature branch using the GitHub button, or, if it still exists and nobody needs it:

```bash
git push origin --delete test/QA-123-customer-validation
```

After squash merge, `git branch -d` may refuse because the original commit IDs are not ancestors of `main`. Verify the merged PR and confirm there are no additional local or remote commits to preserve before using `git branch -D` (Section 9).

### Branch and commit naming

| Branch prefix | Example purpose |
| --- | --- |
| `feature/` | New functionality |
| `fix/` | Bug fix, including broken test infrastructure |
| `hotfix/` | Urgent fix for a deployed or integration issue |
| `test/` | New or improved test coverage |
| `refactor/` | Internal restructuring without intended behavior changes |
| `docs/` | Documentation |
| `chore/` | Tooling, configuration or dependency maintenance |

Follow the team's conventions. Prefer one logical change per commit and one coherent task per PR. A local WIP commit can be useful; use squash merge or an agreed history-cleanup policy if necessary. Do not mix unrelated refactoring with an urgent fix.

## 4. Inspecting changes with diff and log

### Before committing: git diff

```bash
# Unstaged changes in a specific tracked file:
git diff -- docs/framework/README_ENTITY_DISCOVER_ARCHITECTURE_GUIDE.md
```

Use this after editing a file and before staging it, to review exactly what changed. The `--` separates revision/options from file paths. Lines beginning with `-` were removed; `+` lines were added. It does not modify any files.

| Command | Comparison |
| --- | --- |
| `git diff` | Working directory vs staging area (unstaged tracked changes). |
| `git diff -- file.py` | Same, limited to a specific path. |
| `git diff --staged` | Staging area vs HEAD (what is ready to commit). |
| `git diff --cached` | Same as `--staged`. |
| `git diff --staged -- file.py` | Staged changes to one file. |
| `git diff HEAD` | Working directory vs HEAD (staged and unstaged tracked changes). |
| `git diff HEAD -- file.py` | Both kinds of tracked changes for one file. |
| `git diff --name-only` | Names of files with unstaged tracked changes. |
| `git diff --stat` | Summary of unstaged changes by file. |
| `git diff --check` | Check unstaged changes for whitespace errors and conflict markers. |

Untracked files are not included in ordinary diff output; discover them with `git status`. A blank diff may mean your changes are already staged, not that they are gone.

### After committing: inspect what will go into the PR

```bash
git fetch origin
git diff origin/main...HEAD
git diff --name-only origin/main...HEAD
git diff --stat origin/main...HEAD
# Review only workflow configuration changes:
git diff origin/main...HEAD -- .github/workflows/
```

`git fetch` ensures you compare against an updated remote-tracking reference, not a potentially stale local `main`.

### Two dots vs three dots

```text
         B --- C   origin/main
        /
A ------
        \
         D --- E   HEAD (your branch)
```

| Command | Meaning |
| --- | --- |
| `git diff origin/main...HEAD` | Compare A with E (merge base vs your branch tip). Typical GitHub PR-style review. |
| `git diff origin/main..HEAD` | Compare C with E (current branch snapshots). May show main-only changes as absent from your branch. |
| `git diff origin/main HEAD` | Same endpoint comparison as the two-dot diff above. |
| `git log origin/main..HEAD` | Commits reachable from HEAD but not origin/main. |
| `git log HEAD..origin/main` | Commits reachable from origin/main but not HEAD. |
| `git log --left-right origin/main...HEAD` | Commits unique to either side. |

**Important:** Two-dot and three-dot syntax mean different things in `git log` and `git diff`. A PR-style diff shows the net change since the merge base, not necessarily every individual change you personally authored.

### Inspect commit history

```bash
git log --oneline --graph --decorate --all -10
git log -p -- tests/customers/api/
git log --oneline -- .github/workflows/
git show <commit-hash>
git diff HEAD~1 HEAD
```

- `--oneline`: condensed commit messages and hashes.
- `--graph`: ASCII branch/merge graph; `--decorate`: branch/tag labels.
- `--all`: include all refs; `-10`: limit to ten commits.
- `git show`: inspect a specific commit and its changes.
- Press `q` to exit Git's pager, or use `git --no-pager log ...`.

QA use case: CI passed yesterday but fails today. Compare commits, inspect changed test files or workflow YAML, and identify where to start investigating. Use `git bisect` for systematic regression isolation (Section 10).

## 5. Fetch, pull, merge and rebase

| Command | Effect |
| --- | --- |
| `git fetch origin` | Updates remote-tracking references according to configured refspecs. Does not integrate into your branch. |
| `git pull` | Fetches and integrates into the current branch using the selected/configured strategy (merge, rebase or fast-forward-only). |
| `git pull --ff-only` | Updates only when a fast-forward is possible or already up to date; refuses divergent history. |
| `git merge origin/main` | Integrates downloaded main history into your current branch without rewriting existing commits. |
| `git rebase origin/main` | Replays your branch's relevant commits on top of downloaded main; rewritten commits get new IDs. |

### Why use git pull --ff-only on main?

```text
Fast-forward:       local A --- B --- C remote
                    local can move directly to C

Divergence:                  B local
                            /
                           A
                            \
                             C remote
                    no direct fast-forward possible
```

Multiple teammates committing to remote `main` do not by themselves cause a refusal. Your local `main` can simply move forward as long as it has no divergent local commits. If it refuses, investigate rather than blindly resetting or force-pushing.

`git pull origin main` is valid, but without an explicit strategy it depends on configuration and history. Use `git pull --ff-only origin main` when you intend only to advance local main.

### Merge or rebase your feature branch

Imagine you created a branch on Monday and teammates merged new code on Tuesday. Integrate their changes before final validation so you can test the combined behavior.

```bash
# On your feature branch, with a clean working tree:
git fetch origin
# Choose ONE:
git merge origin/main
# OR, for a private branch under a rebase-based policy:
# git rebase origin/main
```

```text
Before:       A --- B --- C  main
               \
                D --- E      feature

Merge:        A --- B --- C  main
               \           \
                D --- E --- M feature

Rebase:       A --- B --- C  main
                           \
                            D' --- E' feature
```

| Situation | Recommended approach |
| --- | --- |
| Shared branch with multiple contributors | Merge, unless the team explicitly coordinates another strategy. |
| Private feature branch | Merge or rebase according to team policy. |
| Protected main | Fast-forward-only local updates; integrate changes through approved PRs. |
| First push after a local rebase | Normal `git push -u origin <branch>` is usually sufficient. |
| Previously published private branch whose history you rewrote | Inspect the remote and use `git push --force-with-lease` only if authorized and intentional. |

`--force-with-lease` checks the remote ref against an expected value (normally your remote-tracking ref). It is safer than `--force`, but it is not a guarantee against losing another person's work, especially if a background fetch updated that reference. Never use force-push as a routine solution to a rejected push.

Shortcut on your private feature branch: `git pull --rebase origin main`. This fetches and rebases onto the fetched main. The two-command approach is easier to inspect.

### Pull Request merge strategies

| GitHub strategy | Result on main |
| --- | --- |
| Merge commit | Retains feature commits and creates a merge commit. |
| Squash and merge | Combines PR changes into one new commit. Original feature commit IDs are not preserved as ancestors. |
| Rebase and merge | Replays feature commits individually on main with new commit IDs. |

Team policy determines the permitted approach. Local merging/rebasing a feature branch is separate from the hosting platform's PR merge strategy.

## 6. Stash and urgent hotfix workflow

### Stash essentials

Use stash when you need a clean working tree temporarily but your work is not ready to commit. A stash is local, not a remote backup, and not automatically tied to restoring on the original branch.

| Command | Purpose |
| --- | --- |
| `git stash` | Save tracked staged/unstaged changes. Does not include ordinary untracked files. |
| `git stash push -u -m "WIP: checkout tests"` | Also save untracked nonignored files, with a label. |
| `git stash list` | List saved stashes. |
| `git stash show -p 'stash@{0}'` | Inspect the latest stash's tracked patch. Add `-u` to show saved untracked content too. |
| `git stash apply 'stash@{0}'` | Restore a selected stash, retaining the stash as a backup. |
| `git stash pop 'stash@{0}'` | Restore and remove the selected stash if successful. |
| `git stash apply --index 'stash@{0}'` | Also attempt to restore the previous staged state. |
| `git stash drop 'stash@{0}'` | Delete a selected stash after verifying it is no longer needed. |

Stash indices change as entries are added or removed. `-u` does not include ignored files such as typical `.env` or virtual environments. Avoid using `-a` indiscriminately because it includes ignored files too.

### Step-by-step hotfix workflow

**Scenario:** You are working on `feature/checkout-tests` when a critical bug needs an urgent fix on `main`.

**1. Shelve unfinished feature work.**

```bash
git status
git stash push -u -m "WIP: checkout tests"
git stash list
git status
```

Only stash if there are changes to save. Check the entry exists and the working tree is ready for switching.

**2. Start from the correct base.**

```bash
git switch main
git pull --ff-only origin main
git switch -c hotfix/critical-checkout-bug
```

This assumes `main` is the appropriate hotfix base. If production is deployed from an older release, branch from the designated release branch/tag and follow the team's release/backport policy.

**3. Fix the issue, validate it and publish the fix.**

```bash
# Make the fix and add/update its regression test.
# Run the affected tests first, then appropriate smoke coverage.
pytest -m smoke
git status
git diff
git add .
git diff --staged
git commit -m "fix: resolve critical checkout bug"
git push -u origin hotfix/critical-checkout-bug
```

**4. Open a PR targeting main** (or the approved release branch). Follow the required hotfix approvals, quality gate, deployment and post-deployment verification. Urgency does not automatically bypass CI or review.

**5. Resume feature development.** You can do this while the hotfix PR is still open, provided your hotfix working tree is clean.

```bash
git switch feature/checkout-tests
git stash list
# Verify this is the labeled feature stash; adjust index if needed.
git stash pop 'stash@{0}'
git status
```

If pop conflicts, the stash is normally retained. Resolve the files and inspect the result; do not pop again blindly. If there was no stash created in Step 1, skip restoration.

**6. Bring in the hotfix once merged into main.** Commit or stash your current edits first, then stay on the feature branch:

```bash
git fetch origin
git merge origin/main
# If you stashed again, restore the correct stash after integration.
```

Rerun the affected tests. Clean up the hotfix branch when safe using Section 3.

## 7. Working on multiple tickets with worktree

`git worktree` creates another working directory connected to the same Git repository. This is a useful alternative to stash when two tasks must remain open simultaneously.

From the original repository, even with unfinished feature edits:

```bash
git fetch origin
git worktree add -b hotfix/urgent-checkout ../checkout-hotfix origin/main
git worktree list
cd ../checkout-hotfix
```

The original working tree remains untouched. The new directory has its own checkout and index but shares Git objects, branch refs and stashes. Git normally prevents checking out the same branch in two worktrees.

### QA/SDET runtime isolation

A Git worktree does **not** isolate the execution environment by itself. For simultaneous test runs:

- Use a separate virtual environment per worktree, or separate test-runner containers/images.
- Use distinct Docker Compose project names, ports, database/test-data namespaces and volumes where appropriate. A different project name alone does not isolate fixed host ports, explicitly named resources or external services.
- Isolate report, log, Allure and Playwright artifact directories.
- Do not let one suite clean up data owned by another. Use an execution lock if an environment cannot safely support concurrent runs.

Enterprise teams often give CI jobs independent checkouts and runners, and provision separate ephemeral environments or isolate shared test resources. The exact design depends on cost, infrastructure and test requirements.

When the hotfix is finished, verify the PR and clean working tree, stop any dedicated infrastructure, then from the original directory:

```bash
git worktree remove ../checkout-hotfix
git worktree list
```

Removing the directory through Git does not delete the branch itself. Use the normal branch cleanup steps after merge.

## 8. Undoing changes and recovering work

**Check `git status` and `git diff` before undoing anything.** Preserve work you may need with a commit, stash, or backup branch as appropriate.

| Situation | Command | Effect |
| --- | --- | --- |
| Accidentally staged a file | `git restore --staged -- file.py` | Unstages it, keeps working edits. |
| Discard unwanted unstaged edits | `git restore -- file.py` | Restores from index; discards unstaged changes. |
| Correct last unpublished commit | `git commit --amend` | Replaces the last commit with a new one, including newly staged changes. |
| Undo last unpublished commit, keep staged work | `git reset --soft HEAD~1` | Moves branch back one commit; leaves index and files unchanged. |
| Undo last unpublished commit, keep work unstaged | `git reset HEAD~1` | Moves branch and resets index; leaves working files. |
| Undo a shared commit safely | `git revert <commit-hash>` | Creates a new inverse commit. Use a fix branch and PR for protected main. |
| Recover a commit after reset or rebase | `git reflog` | Find prior local HEAD/ref positions. |

### Destructive commands — use with care

| Command | Risk |
| --- | --- |
| `git reset --hard <commit>` | Moves current branch (or detached HEAD), resets index and tracked files; discards uncommitted tracked edits and can remove obstructing untracked paths. |
| `git clean -fd` | Permanently removes nonignored untracked files/directories. Preview with `git clean -nd`. |
| `git clean -fdx` | Also removes ignored files, potentially including virtual environments, local configs and test artifacts. Avoid as a routine cleanup. |
| `git branch -D <branch>` | Force-deletes a local branch regardless of merged history. |
| `git push --force` | Can overwrite remote commits. Avoid; see Section 5. |

`git reset --hard` is not a universal recovery command. Commits may be recoverable through reflog, but edits that were never committed or stashed generally are not.

### Reflog recovery

```bash
git reflog
# Identify the lost commit hash, then create a recovery branch:
git branch recovery/QA-123 <commit-hash>
git show <commit-hash>
```

This preserves the recovered commit without resetting your current branch. Reflog is local and expires according to configuration (commonly 90 days for reachable entries and 30 days for unreachable entries). It is not a backup strategy.

### Cherry-pick a specific fix

Use `git cherry-pick` when a commit is needed on another branch without merging the entire source branch (for example, backporting a CI fix).

```bash
git switch main
git pull --ff-only origin main
git switch -c fix/backport-test-fix
git cherry-pick <commit-hash>
```

Cherry-pick applies the selected commit's change and normally creates a new commit. Check for prerequisite commits and test the result. If it conflicts, resolve and stage files, then use `git cherry-pick --continue`, or cancel with `git cherry-pick --abort`.

## 9. Troubleshooting common Git problems

### A. Merge or rebase conflicts

A conflict means Git needs a human decision about incompatible changes. Inspect the conflicting files and combine the intended behavior, not just the text.

```bash
git status
# Edit each conflicting file, remove conflict markers, run relevant tests.
git add <resolved-file>
# For a merge:
git merge --continue
# OR for a rebase:
# git rebase --continue
```

Conflict markers look like this:

```text
<<<<<<< HEAD
one side's content
=======
other side's content
>>>>>>> incoming-reference
```

| Operation | `--ours` | `--theirs` |
| --- | --- | --- |
| Merge main into feature | Current feature branch | Incoming main |
| Rebase feature onto main | Rebased state, starting from main | Feature commit currently being replayed |

`git checkout --ours -- file.py` or `git checkout --theirs -- file.py` selects one side of the conflicted file. This may discard important changes; inspect before choosing. Use `git merge --abort` or `git rebase --abort` to cancel the corresponding operation if needed. Rebase may stop several times. Stash conflicts have no `stash --continue`; resolve and stage manually.

### B. Push rejected (non-fast-forward)

```bash
git fetch origin
git status
git log --oneline --left-right HEAD...@{upstream}
```

Run the last command only if an upstream exists. If teammates pushed new commits, integrate the upstream (for example `git merge '@{upstream}'` on your feature branch), retest and push. If you intentionally rewrote your own previously pushed branch, follow the force-with-lease safeguards in Section 5. If there is no upstream, see Section 11.

### C. Local main is ahead or has diverged

Do not immediately run `git reset --hard`.

```bash
git switch main
git fetch origin
git status
git log --oneline origin/main..HEAD
git log --oneline HEAD..origin/main
```

If local commits are accidental, preserve them first. Only if the working tree is clean and you have confirmed local main should exactly mirror the remote:

```bash
git branch backup/main-before-reset
git reset --hard origin/main
```

The backup branch preserves commits, not uncommitted edits. If the local commits are useful, create a feature branch or cherry-pick them onto an appropriate branch. Do not push accidental main commits directly to a protected branch.

### D. Uncommitted work on main while remote main is behind or ahead

If you accidentally edited files on `main`, move the work onto a new task branch before updating main:

```bash
git switch -c feature/recover-my-work
git status
git add <intended-file>
git commit -m "test: preserve work on feature branch"
# Ensure all remaining work is committed or safely stashed first.
git switch main
git pull --ff-only origin main
git switch feature/recover-my-work
git merge main
```

This assumes no accidental local main commits; if there are any, use the previous scenario too. Staging alone is not a safe checkpoint for switching branches.

### E. Detached HEAD

Checking out a commit or `origin/main` directly can detach HEAD. This is useful for inspection, but new commits need a branch if you want to keep them easily.

```bash
# Still at the commit you want to preserve:
git switch -c recovery/detached-work
# Already switched away? Find the commit with git reflog, then:
# git switch -c recovery/detached-work <commit-hash>
```

### F. Branch deletion refused after squash merge

`git branch -d` checks merged ancestry against the upstream, or HEAD if no upstream exists. It can refuse after squash merge, or succeed with a warning if the branch was pushed but not merged into HEAD. Neither outcome proves the PR was merged.

Check the PR on GitHub, verify it contains the work you intended to preserve, and inspect any commits added since the merged PR (including unpushed ones). If everything is safe:

```bash
git switch main
git pull --ff-only origin main
git branch -D feature/old-task
git fetch origin --prune
```

### G. Rebase brings in unrelated commits

This can happen when a branch was based on a different feature branch, especially after that parent was squash-merged. Stacked PRs can be legitimate, but their base and integration order must be intentional.

If a rebase is currently in progress and you want to stop:

```bash
git rebase --abort
```

Then, with a clean working tree, create a fresh branch from updated main and cherry-pick only the intended commits (oldest first):

```bash
git switch main
git pull --ff-only origin main
git switch -c fix/QA-123-clean
git cherry-pick <commit1> <commit2>
```

Inspect `git diff origin/main...HEAD`, test and push. Keep the old branch until recovery is verified. Branching from an old good commit alone does **not** undo newer changes when merged into main; use revert or explicit corrective commits for that purpose.

## 10. Git for QA debugging

### Blame — where did this line come from?

```bash
git blame -L 20,40 -- tests/ui/pages/shopping/cart_page.py
git show <commit-hash>
```

`git blame` annotates lines with the commits that last changed them. Use it to understand context and find the associated change, not to assign personal blame.

### Bisect — which commit introduced a regression?

**Scenario:** Checkout tests pass on a known earlier commit but fail on the current revision. Git can use a binary search to narrow down the regression.

Start with a clean working tree and known good/bad revisions:

```bash
git bisect start
git bisect bad HEAD
git bisect good <known-good-commit>
```

Git checks out a candidate commit. Run a focused reproducible test on it:

```bash
pytest tests/ui/tests/ -k checkout -x
```

If the relevant behavior passes, run `git bisect good`; if it fails for the same regression, run `git bisect bad`. If the revision cannot be tested, use `git bisect skip`. Repeat until Git identifies the first bad candidate or a set of possible candidates.

```bash
git bisect log
git bisect reset
```

For automation, supply a script that returns 0 for good, 1–127 except 125 for bad, and 125 for untestable revisions:

```bash
git bisect run /path/to/regression-check.sh
```

Do not blindly classify every pytest failure as the target regression: missing dependencies, collection errors, flaky tests and changed test data can invalidate the result. Keep the reproducer available across revisions (for example outside the bisected checkout), pin relevant dependencies, and rebuild code/images when the tested revision changes. Finish with `git bisect reset`.

## 11. Remotes and upstream tracking

```bash
git remote -v
git branch -vv
git fetch origin --prune
```

Pruning removes stale remote-tracking refs under normal branch refspecs, not local feature branches or remote branches themselves. Preview with `git fetch origin --prune --dry-run`. Custom refspecs may change what is pruned.

### First push and tracking

```bash
git push -u origin feature/QA-123
```

Once an upstream is established, `git pull` uses that upstream by default, and `git push` usually targets it or the same-named remote branch depending on configuration. **Pulling on your feature branch does not automatically integrate main.** Use Section 5 for that.

For an existing remote branch, set tracking without pushing:

```bash
git branch --set-upstream-to=origin/main main
```

Optional personal setting for automatic upstream setup on default pushes (supported with compatible Git versions and push defaults):

```bash
git config --global push.autoSetupRemote true
```

### Multiple remotes (GitHub and GitLab)

```bash
git remote add gitlab <gitlab-url>
git remote -v
git fetch --all
git fetch gitlab
git push gitlab feature/QA-123
```

To change an existing remote URL: `git remote set-url origin <new-url>`. Avoid `-u` on a secondary push unless you intend to change the branch's upstream.

Optional combined push remote:

```bash
git remote add both <gitlab-url>
git remote set-url --add --push both <github-url>
git remote set-url --add --push both <gitlab-url>
git push both feature/QA-123
```

This fetches from its configured fetch URL and pushes to both push URLs when requested. A multi-remote push is not atomic across servers: one can succeed while the other fails. Separate remotes are clearer for most teams; follow company rules for mirroring.

## 12. Team workflow, CI and security

### Protect the integration branch

In GitHub branch protection/rulesets, configure the policies required by your team: PR reviews, required CI status checks, conversation resolution, stale review handling, restrictions on force pushes/deletion and controlled bypass. Require branches to be up to date or use a merge queue if your integration policy needs it. Availability and exact setting labels depend on plan and platform.

GitHub protection applies to the remote, not local commits. A required quality gate should accurately reflect the checks that must pass.

### What happens after a push and PR?

```text
Feature push -> configured CI (if any)
Open/update PR -> required validation -> review + quality gate -> merge
Merge into main -> configured post-merge tests / deployment / scheduled validation
```

Triggers and test selections are defined by the repository's workflow files, not by Git. A push to a branch with an open PR may trigger PR synchronization checks; it does not necessarily trigger all workflows.

Typical QA/SDET strategy: quick unit, preflight, smoke and targeted integration checks on PRs; broader regression, cross-browser, security or performance suites on merge or a schedule according to risk. A green gate means configured checks passed, not that all defects are impossible.

Example GitHub Actions workflow for a simple Python project (adapt dependency installation, infrastructure and test selection to the repository; action major tags are illustrative, pin verified SHAs under company policy):

```yaml
name: PR validation
on:
  pull_request:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - run: python -m pip install -r requirements.txt
      - run: python -m pytest -q
```

Add the appropriate check as required in branch protection. Test dependencies and test environment provisioning must exist for this example to work. A standalone SDET framework may run against a deployed test environment or a Docker-provisioned stack; Git alone does not provision either.

### Secrets and ignored files

Never commit API keys, passwords, production data or tokens. Use local environment variables or ignored `.env` files and the CI platform's secrets store.

Example `.gitignore` (adapt paths to your repo):

```gitignore
.env
.env.*
!.env.example
.venv/
__pycache__/
.pytest_cache/
reports/
test-results/
```

A sanitized `.env.example` can document required variable names without secrets. CI example:

```yaml
- name: Run API tests
  env:
    WC_CONSUMER_KEY: ${{ secrets.WC_CONSUMER_KEY }}
    WC_CONSUMER_SECRET: ${{ secrets.WC_CONSUMER_SECRET }}
  run: python -m pytest tests/customers/api
```

Python accesses configuration with `os.getenv("WC_CONSUMER_KEY")` or a centralized configuration loader. Check logs, screenshots and browser traces for sensitive information before uploading them as artifacts, particularly in public repositories.

`.gitignore` does not untrack already committed files. If a secret was committed, revoke/rotate it immediately, notify the appropriate owner and follow the repository's incident/history-cleanup procedure. Deleting the file in a later commit is not sufficient.

## 13. Pre-commit, line endings and aliases

### Pre-commit hooks

The versioned `.pre-commit-config.yaml` file declares shared hooks, versions and options. When a project provides it, install hooks in your active environment:

```bash
python -m pip install pre-commit
pre-commit install
pre-commit run              # normally staged files
pre-commit run --all-files  # full tracked-file check, useful after config changes
```

Installed hooks run during `git commit`. If a formatter changes files, review the changes, stage the intended fixes, then retry your commit. A second attempt is not guaranteed to pass if other checks still fail.

`git hook run pre-commit` directly invokes an installed hook on supported Git versions. Local hooks can be bypassed (`--no-verify`), so required CI checks remain important. Do not bypass hooks merely to get a green commit; follow team policy. Teams may share centrally maintained hook definitions, but each project still needs appropriate versioned configuration.

### Line endings (Windows and Linux)

LF and CRLF are different newline representations. A versioned `.gitattributes` policy is preferable to relying entirely on developers' global Git configuration, particularly for Python, YAML and Docker shell scripts.

Example (adopt with team agreement):

```gitattributes
* text=auto
*.py text eol=lf
*.md text eol=lf
*.yml text eol=lf
*.yaml text eol=lf
*.sh text eol=lf
*.bat text eol=crlf
*.png -text
```

Inspect settings and file state:

```bash
git config --show-origin --get core.autocrlf
git ls-files --eol
git check-attr -a -- path/to/file.py
```

After deliberately changing repository normalization rules, start with a clean working tree and use a dedicated branch/commit:

```bash
git add .gitattributes
git add --renormalize .
git diff --staged --stat
git diff --staged
git commit -m "chore: normalize repository line endings"
```

Do not change global `core.autocrlf` just to suppress a warning. Explicit attributes control paths they cover; other paths can still depend on local config. Renormalization stages tracked content using current attributes; inspect it for unexpected changes.

### Optional Git aliases

```bash
git config --global alias.lg "log --oneline --graph --decorate --all -10"
git config --global alias.fp "fetch origin --prune"
git lg
git fp
```

Inspect/edit with `git config --global --edit`, redefine an alias by running its config command again, or remove it with `git config --global --unset alias.lg`. Optional `git config --global fetch.prune true` enables automatic pruning on fetch. Global configuration affects all repositories for your user; omit `--global` for repository-local config. Aliases do not inherently disable the pager.

## 14. PyCharm workflow and daily checklist

PyCharm provides equivalents for many Git operations. Use the branch selector to switch/create branches, the Git menu to fetch/pull, the Commit window to stage/review changes, and the Push dialog to publish them. Common Windows shortcuts include Ctrl+K (commit) and Ctrl+Shift+K (push), depending on the keymap. Create and review the PR on the hosting platform. If available, configure IDE warnings when committing to protected branches.

The CLI remains valuable for troubleshooting and understanding exactly what the IDE does.

### Everyday QA checklist

- Before work: verify branch and working state; update the correct base and create a task branch.
- During work: inspect changes with `git diff`; keep test data, environments and generated artifacts isolated.
- Before commit: run relevant tests; review staged changes and check for secrets/unrelated modifications.
- Before merging: fetch and sync as appropriate, review the PR diff, rerun affected tests, verify approvals and quality gate.
- After merging: update local main and clean up verified merged branches.
- When something goes wrong: start with `git status`, then `git diff`, `git log` and `git reflog` as appropriate. Never blindly reset or force-push.

### Further reading

- [Official Git reference](https://git-scm.com/docs)
- [Pro Git book](https://git-scm.com/book/en/v2)
- [GitHub documentation](https://docs.github.com/)
- [pre-commit documentation](https://pre-commit.com/)
