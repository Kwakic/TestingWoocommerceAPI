# Git Workflow Guide for QA Engineers (Advanced)

---

# 🚀 Overview
This guide expands the standard Git workflow with:

1.  Changing Remotes, Dual GitHub + GitLab setup
2.  PyCharm-Only Workflow (No Terminal)
3.  Git CLI Workflow Guide (Terminal) Beginner-Friendly
4.  Troubleshooting: Rebase Pulling in Old
5.  Protect main Branch (GitHub)
6.  Continuous Integration (CI) with Pytest
7.  Secrets Management
8.  Clean Commit Strategy
9.  Check history of commits
10.  Git Shortcuts logs and prune
11.  Rebase vs Merge
12.  git cherry-pick
13.  Switching Branches
14.  Upstream Branch (Tracking)
15.  Automating of the creation and tracking of remote branches
16.  Automatically normalizing line endings
17.  Configuration file .pre-commit-config.yaml
18.  Git Fetch vs. Git Pull


--

# 🌐 1. Changing Remotes, Dual GitHub + GitLab setup

##   🔄  Changing Remotes

To interact with a specific remote, include its name (e.g., origin or GitLab) in your command:

* **To Push:**

    * Push to GitHub: `git push origin <branch-name>`
    * Push to GitLab: `git push GitLab <branch-name>`


* **To Pull:**

    * Pull from GitHub: `git pull origin <branch-name>`
    * Pull from GitLab: `git pull GitLab <branch-name>`


* **To Fetch Updates:**

  * `git fetch GitLab` or `git fetch origin`
  * Get updates from all remotes at once: `git fetch --all`

### Setting a Default Remote (Upstream)**

If you want a branch to always use a specific remote by default (so you can just type `git push` or `git pull`),
you can set the "**upstream**" tracking:

```
# Link the current local branch to GitLab's main branch
git push -u GitLab main
```

**Note:** The `-u `(or `--set-upstream`) flag remembers your choice for that specific branch.

Once the upstream is set, you can use just `git pull `or `git push` without specifying the remote (`GitLab`) or branch
(`main`) each time.

---

## 🔧 Setup "both" remote

```bash
git remote add both <GitLab-URL>
git remote set-url --add --push both <GitHub-URL>
git remote set-url --add --push both <GitLab-URL>
```

###  Push to both

```bash
git push both
```

### PyCharm alternative
- Open Push dialog (Ctrl+Shift+K)
- Select remote (origin / github)


---
# 🧑‍💻 2. PyCharm-Only Workflow (No Terminal)

### Daily flow

1. Checkout main (bottom-right branch menu)
2. Click **Pull**
3. Create new branch:
   - Click branch name → New Branch
4. Work on code
5. Commit:
   - Ctrl+K → write message → Commit
6. Push:
   - Ctrl+Shift+K → Push
7. Create PR in GitHub UI
8. Merge PR
9. Delete branch (GitHub button)
10. Delete local branch:
   - Branch menu → Delete

👉 No terminal needed

---

##  🔁 Standard Workflow

```
main → create branch → work on code → commit → push → PR → merge → delete branch
```

---
# 🧑‍💻 3. Git CLI Workflow Guide (Terminal) Beginner-Friendly

A step-by-step guide to safely work with Git using branches, commits, and Pull Requests.

---

### 📊 Visual Flow (Mental Model)

```
          (origin/main)
                │
                ▼
        ┌──────────────┐
        │   main       │  ← always updated
        └──────┬───────┘
               │
               ▼
   git checkout -b fix/xxx
               │
               ▼
        ┌──────────────┐
        │ fix/xxx      │  ← your work happens here
        └──────┬───────┘
               │
     (commit / stash)
               │
               ▼
     git fetch origin
               │
               ▼
     git rebase origin/main
               │
               ▼
        (resolve conflicts)
               │
               ▼
          git push
               │
               ▼
        Pull Request (PR)
               │
               ▼
        Squash & Merge
               │
               ▼
        ┌──────────────┐
        │   main       │  ← updated again
        └──────────────┘
```
💡 Think of it like:

* `main` = source of truth
* `fix/xxx `= your safe workspace
* **PR** = controlled integration

---

## 🔹Step 1. ✅ Start from updated `main`

```bash
git checkout main
git pull origin main
```

💡 Do this before starting any new work to stay in sync with the team.

If you see:

`There is no tracking information for the current branch`

Run once:

`git branch -u origin/main
`

---

## 🔹Step 2. 🛠️ Create a new branch

```bash
git checkout -b fix/bug_ticket_1235
```

💡 Use one branch per ticket/feature

---

## 🔹 Step 3. 👩🏻‍💻 Work on code

Make your changes in the codebase/ IDE (e.g., PyCharm).

---

## 🔹 Step 4. 📝 Save your work (Commit or Stash)

Before syncing with main, your working directory must be clean.

### ✅ Option 1: Commit (recommended if code is stable)

```bash
git add .

pre-commit run # staged files
# or:
pre-commit run --all-files

git commit -m "WIP: working on login"
```

💡 If pre-commit modifies files → run `git add . `again


---

### 🟡 Option 2: Stash (if work is not ready)

#### ✅ Why this is better than committing?

* Keeps history clean (no cluttering your history): You don't have to make messy commits like "saving progress" or
"work-in-progress" etc. just to get a merge to work.

* If your code is a mess and you don't want to commit it yet, the standard "Git Pro" move is to use `git stash`.
It’s like a temporary drawer for your work (pause).

This allows you to pull in updates from main even if you have half-finished code sitting in your fix branch.

Stash your work. Move your uncommitted changes to a temporary storage area by running following command:

```
git stash

# Restore later before push step:
git stash pop

# Include untracked files:
git stash -u
```

* **Safety first**: If `git stash pop` causes a conflict with the new code from `main`, Git will tell you immediately.
* **Efficiency**: You never have to leave your fix branch or `checkout` to `main` at all.

### Key Commands for stash Flow

* `git stash`: Saves your uncommitted changes and resets your branch to a "clean" state.
* `git stash list`: Shows you all the bits of work you currently have tucked away.
* `git stash pop`: Re-applies the most recent stash and removes it from your storage list.
* `git stash apply`: Re-applies the stash but keeps it in storage (useful if you're nervous and want a backup).

☝️ Tip: If you have brand-new files that you haven't even "added" yet, use `git stash -u` to make sure those untracked files are tucked away too.


---

## 🔹 Step 5. 🔄 Sync with `main` (IMPORTANT)

### ⬇️ Download the latest updates: Grab everything from the server.

To avoid conflicts and ensure your current branch (fix/bug_ticket_1235) is up-to-date:

👉 Choose **ONE workflow** and stick to it

### 🟢 Option A (Beginner-friendly — recommended)

```
git checkout main
git pull origin main

git checkout fix/bug_ticket_1235
git merge main
```

### 🔵 Option B (Pro workflow — faster)

In Git, `git pull` is essentially a combination of `git fetch` followed immediately by `git merge`.
By breaking these apart, you gain more control:


```
git fetch origin

# check for possible changes made in main branch
git log HEAD..origin/main --oneline

git merge origin/main
```

or (cleaner history):

```
git fetch origin

# check for possible changes made in main branch
git log HEAD..origin/main --oneline

git rebase origin/main
```

---

### ❗ If used `git stash` bring your work back: Pop your changes out of storage and put them back on top.

```
git stash pop
```
* **Safety first**: If `git stash pop` causes a conflict with the new code from `main`, Git will tell you immediately.

---

### ⚠️ If conflicts happen
`git status`

Fix files manually, then:

### For merge:

```
git add .
git commit
```

### For rebase:

```
git add .
git rebase --continue
```

---

## 🔹 Step 6. 🚀 Push your branch

First push:
```bash
git push -u origin fix/bug_ticket_1235
```

Next pushes:
```
git push
```

⚠️ If you used rebase:
```
git push --force-with-lease
```

#### 💡 Why force push is needed

After `git rebase`: Git rewrites commit history

So normal push won’t work → you MUST use: `git push --force-with-lease`

---

## 🔹 Step 7. 🚨 Final sync before PR

To avoid conflicts and ensure your branch is up-to-date.

```
git fetch origin

# check for possible changes made in main branch
git log HEAD..origin/main --oneline

git merge origin/main
```

or (cleaner history):

```
git fetch origin

# check for possible changes made in main branch
git log HEAD..origin/main --oneline

git rebase origin/main
```

👉 Ensures:
* no conflicts
* PR will merge cleanly

---

## 🔹 Step 8. 🛎️ Create Pull Request (PR)

- Go to GitHub
- Click "**Create Pull Request**"
- Add description
- Submit PR

---

## 🔹 Step 9. 🧬 Merge PR

Recommended:

* ✅ Squash and merge

👉 Keeps history clean

---

## 🔹 Step 10. 🗑️ Cleanup (Delete branch)

### 🌿 Delete remote branch (GitHub)
* **Option 1:** Click "**Delete branch**" on GitHub side

* **Option 2:**  in CLI run this command: `git push origin --delete fix/bug_ticket_1235`


### 🌿 Delete local branch (Local Cleanup)

If you used "`Squash and Merge`" on GitHub, your local machine might think your branch isn't fully merged yet
(because the commit IDs changed during the squash).

```bash
# 1. Switch to another branch (usually main):
git checkout main
# 2. Pull last update:
git pull origin main
# 3. Delete the branch:
git branch -d fix/bug_ticket_1235
# or force delete if needed:
git branch -D fix/bug_ticket_1235
```

### ⚠️ Important Notes

- `git branch -d` → safe delete (only if merged)
- `git branch -D` → force delete (use carefully)

📝 Note: If `git branch -d fix/bug_ticket_1235` gives you an error, use the capital `-D` to force delete it, since you know the work is safe on GitHub:

---
### 📌 Summary

You only delete the branch **after merge**.

Deleting earlier = losing your work.


---

## 🔹 Step 11. 🔄 Update local `main`

 After you deleted the branch on GitHub and locally, your local `main` is still technically "behind" what's on the server.

 You should run one final` git pull origin main `while on your `main` branch to bring that "**Squash and Merge**" commit down to your machine.

---

## 🔹 Step 12. 🧹 Clean stale branches (optional)

`git fetch origin --prune` (or the shorthand git fetch -p) is safe for most standard workflows. It is a common
housekeeping command used to keep your local environment synchronized with the remote.

### 💡 What it does

* Fetches new data: Like a regular git fetch, it downloads new commits and branches from the remote.
* Deletes "stale" references: It removes your local remote-tracking branches (e.g., origin/feature-branch) that no longer exist on the remote server.

Not required, but good for cleanup


🔥 If you want to see what will happen without actually deleting anything, you can run a "dry run" first:
```bash
# preview first:
git fetch --prune --dry-run
```
Then run:
```
git fetch origin --prune
```

### 🔎 Why it is safe

* Does not touch local branches: It only deletes references in your refs/remotes/ folder. It will not delete the actual local branches you are working on, even if their corresponding remote branch was deleted.
* No data loss on remote: This command only affects your local machine; it does not delete anything from the remote server.
* Easily reversible: If a remote-tracking branch is accidentally pruned but still exists on the remote, you can simply run git fetch again to restore it

---

## ⚠️ Common Mistakes (and How to Avoid Them)

---

### ❌ 1. “It works on my branch but PR has conflicts”


👉 Cause:
* You didn’t sync with main

✅ Fix:

```
git fetch origin
git rebase origin/main
```
---

### ❌ 2. “Git says: non-fast-forward push rejected”

👉 Cause:
* You rebased but tried normal push

✅ Fix:

```
git push --force-with-lease
```
---

### ❌ 3. “I committed broken or unfinished code”

👉 Cause:
* Using commits as temporary storage

✅ Fix:
```
git stash
```
---

### ❌ 4. “I lost my changes after switching branches”

👉 Cause:
* Uncommitted changes overwritten

✅ Fix:
Always:
```
git add .
# OR
git stash
```
---

### ❌ 5. “Too many messy commits in PR”

👉 Cause:
* Multiple WIP commits

✅ Fix:
Use:

```
Squash & Merge
OR
git rebase -i HEAD~n
```

---

### ❌ 6. “Force push broke my teammate’s work”

👉 Cause:
* Rewriting shared branch history

✅ Rule:
👉 NEVER rebase shared branches
👉 Only rebase your own branch

---

### ❌ 7. “Local branches don’t match remote”

👉 Cause:
* Deleted branches still exist locally

✅ Fix:

```
git fetch --prune
```

---

### ❌ 8. “pre-commit changed files after commit failed”

👉 Cause:
* Hooks modified files

✅ Fix:
```
git add .
git commit -m "..."
```

---

## ⭐ Golden Path (Quick Cheat Sheet)

```
git checkout main
git pull

git checkout -b fix/xxx

# work
git add .
git commit -m "msg"

git fetch origin
git rebase origin/main

git push -u origin fix/xxx
```
---

## 🧠 Key Concepts
* **Commit** → save work permanently
* **Stash** → temporary save
* **Merge** → combine histories (safe)
* **Rebase** → rewrite history (cleaner, but advanced)
* **Force push** → required after rebase

---


## 🎯 Key Takeaways

- Always start from updated main
- Use PRs for everything
- Prefer rebase for clean history
- Protect main branch
- Keep commits clean and small
- Use PyCharm UI for simplicity


---

## ✨ Golden Rule

👉 Always sync with main before opening a PR

👉 Fix conflicts locally — not in shared branches

---

## 📌 Summary

You only delete the branch **after merge**.

Deleting earlier = losing your work.


---

#  ⚠️ 4. Troubleshooting

---

## 🔹 1. Rebase Pulling in Old (Unrelated) Commits

### 🧠 Problem Summary

While rebasing a feature branch (e.g., `fix/bug_ticket_111`), Git may try to replay **old, unrelated commits** such as:

```text
cc5dd5c → ... → b5667d8   (previous feature work)
```

Even though:

* These commits were already pushed
* Already merged via a previous Pull Request
* No longer relevant to your current work

---

### ❗ Root Cause

This happens when your current branch was created from another feature branch instead of `main`.

```text
main
  └── fix/bug_ticket_666  (old work)
         └── fix/bug_ticket_111  (new work)
```

👉 As a result, your branch inherits **all previous commits**, and during rebase Git attempts to replay them.

---

### 🚨 Symptoms

* Rebase starts replaying many old commits
* Conflicts appear for files unrelated to your current task
* Commit list includes work from previous tickets

---

### ✅ What You Actually Want

```text
main → only your new commits (bug_ticket_111)
```

NOT:

```text
main → old commits (bug_ticket_666) → new commits
```

---

## 🛑 Immediate Fix (If You’re Mid-Rebase)

Abort the rebase to return to a safe state:

```bash
git rebase --abort
```

---

## 🔧 Clean Solution (Recommended)

Recreate your branch from a clean `main` and keep only relevant commits.

### 1️⃣ Update main

```bash
git checkout main
git pull origin main
```

---

### 2️⃣ Create a new clean branch

```bash
git checkout -b fix/bug_ticket_111_clean
```

---

### 3️⃣ Cherry-pick only your relevant commits

```bash
git cherry-pick <commit1> <commit2> ...
```

Example:

```bash
git cherry-pick eaeb9d1 b60323f 2c8087c 324f83e c3505bb
```

---

### 4️⃣ Push the clean branch

```bash
git push -u origin fix/bug_ticket_111_clean
```

---

### 5️⃣ Create a new Pull Request

* Base: `main`
* Compare: `fix/bug_ticket_111_clean`

👉 Your PR will now contain only relevant changes.

---

## 🧹 Cleanup (Optional)

Delete the old polluted branch:

```bash
git branch -D fix/bug_ticket_111
git push origin --delete fix/bug_ticket_111
```

---

## 🧠 How to Avoid This Problem

### ✅ Always create branches from `main`

```bash
git checkout main
git pull origin main
git checkout -b fix/new-feature
```

---

### ❌ Avoid creating branches from other feature branches

```text
feature → feature → feature  ❌ (causes history pollution)
```

---

### ✅ Follow this rule

```text
1 branch = 1 feature / 1 ticket
```

---

## 🎯 Outcome

* Clean commit history
* No unrelated conflicts during rebase
* Clear and reviewable Pull Requests
* Predictable Git workflow

---

## 🧠 Key Takeaway

> If your branch contains unrelated commits, don’t fight the rebase — rebuild the branch cleanly from `main`.

---

## 🔹 2. Push Rejected After Rebase (Non-Fast-Forward Error)

### 🧠 Problem Summary

After running a rebase:

```bash
git rebase origin/main
```

You try to push:

```bash
git push
```

And get an error:

```text
! [rejected] non-fast-forward
error: failed to push some refs
```

---

### ❗ Root Cause

Rebase **rewrites commit history**.

```text
Before:
D --- E

After rebase:
D' --- E'   (new commits with new hashes)
```

👉 Even though the content is the same, Git sees them as **different commits**.

---

### 🚨 Symptoms

* Push is rejected with `non-fast-forward`
* Git says your branch is behind or diverged
* Happens after `git rebase`

---

## 🔧 Solution

Use a **safe force push**:

```bash
git push --force-with-lease
```

---

### ✅ Why `--force-with-lease`?

* ✔ Updates remote with your rebased commits
* ✔ Prevents overwriting others’ work
* ✔ Safer than `--force`

---

### ❌ Avoid using:

```bash
git push --force
```

👉 This can overwrite teammates’ commits.

---

## ⚠️ When It’s Safe

Use `--force-with-lease` only when:

* You are working on your **own feature branch**
* No one else is pushing to that branch
* The branch is not shared

---

## ❌ When NOT to Use It

* Shared branches used by multiple developers
* `main` or protected branches
* Team-critical branches

---

## 🧠 How to Avoid This Problem

### Option A — Expect it (normal workflow)

```text
rebase → force-with-lease push
```

---

### Option B — Use merge instead of rebase

```bash
git merge origin/main
git push
```

👉 No history rewrite → no force push needed

---

## 🎯 Outcome

* Your branch updates correctly after rebase
* Clean commit history is preserved
* No accidental overwrites

---

## 🧠 Key Takeaway

> Rebase rewrites history — so a normal push won’t work. Use `--force-with-lease` safely.


## 🔹 3. Detached HEAD (Committed on Wrong Branch)

### 🧠 Problem Summary

You run a command like:

```bash
git checkout <commit-hash>
```

or:

```bash
git checkout origin/main
```

Then make commits…

Later you see:

```text
HEAD detached at <commit>
```

👉 Your commits seem to “disappear” or are not on any branch.

---

### ❗ Root Cause

You are not on a branch — you are in a **detached HEAD state**.

```text
HEAD → specific commit (not a branch)
```

👉 Any commits you make are **not attached to a branch**.

---

### 🚨 Symptoms

* Terminal shows:

  ```text
  (HEAD detached at ...)
  ```
* New commits are not visible in your branch
* `git branch` does not list your new work
* Risk of losing commits

---

## 🔍 Example

```bash
git checkout origin/main   # ❌ detached state
# make changes
git commit -m "some work"
```

👉 That commit is now “floating” — not on any branch.

---

## 🔧 Solution (Recover Your Work)

### ✅ If you just made commits

Create a branch from your current state:

```bash
git checkout -b fix/recovered-work
```

👉 Your commits are now safe and attached to a branch.

---

### ✅ If you already switched away

Find your commit:

```bash
git reflog
```

Then recover:

```bash
git checkout -b fix/recovered-work <commit-hash>
```

---

## 🧠 How to Avoid This Problem

### ❌ Avoid:

```bash
git checkout origin/main
```

---

### ✅ Use instead:

```bash
git checkout main
git pull origin main
```

---

### ✅ Or create a new branch properly:

```bash
git checkout -b fix/new-feature
```

---

## 🧩 Mental Model

```text
HEAD attached   → safe (on a branch)
HEAD detached   → temporary state (danger if committing)
```

---

## 🎯 Outcome

* Lost commits are recovered
* Work is safely attached to a branch
* No accidental data loss

---

## 🧠 Key Takeaway

> If you see “detached HEAD”, stop and create a branch immediately to save your work.

---

## 🔹 4. Local Main "Ahead" of Remote (Accidental Commits on Main)

### 🧠 Problem Summary
You merged a PR on GitHub using **Squash and Merge**, but when you switched back to your local `main` and ran `git pull`,
a **Vim popup** appeared asking for a merge message.

After saving, `git status` shows:

```text
Your branch is ahead of 'origin/main' by 2 commits.
```

👉 Your local history now has a messy "merge loop" that doesn't exist on GitHub.

---

### ❗Root Cause
Two things happened at once:

1. **Accidental Local Commit**: You made a commit (or a typo/save) directly on your local `main` branch.
2. **History Divergence**: GitHub's "Squash and Merge" created a brand new commit ID.

When you pulled, Git saw your local `main` and the remote `main` had different histories and tried to force them
together with a `merge commit`.

---

### 🚨 Symptoms

* A **Vim editor** unexpectedly opens during git pull.
* `git log --oneline` shows a "Merge branch 'main'..." commit.
* `git status` says you are "ahead of origin/main" even though you just pulled.

---

### 🔍 Example:

```bash
# On local main
git commit -m "oops accidental commit"
git pull origin main
# ❌ Vim opens -> you save -> history is now messy
```
👉 Your local main now has your "oops" commit PLUS a "merge" commit.

---

### 🔧 Solution (Align with Remote)
### ✅ Hard Reset to Match GitHub
Since your code is already safely merged into GitHub via the PR, the cleanest fix is to tell your local `main` to
forget its own history and mirror GitHub exactly.

```bash
git fetch origin
git reset --hard origin/main
```
👉 Result: Your local main is now identical to GitHub. The accidental commits and the messy merge are gone.

💡 What this does:
* `fetch`: Grabs the latest info from GitHub.
* `reset --hard`: Force-moves your local `main` pointer to exactly where `origin/main` is, effectively deleting those
* two "ahead" commits and making your history a straight line again.

After you run those, `git status` should say "**Your branch is up to date with 'origin/main'**."


---

### 🧠 How to Avoid This Problem
### ❌ Avoid:
Working or committing directly on the `main` branch.

### ✅ Use instead:
Always create a feature branch for changes. If you realize you made a mistake on `main`, **reset it** before pulling.


```text
Local Main:   A --- B (oops) --- M (Merge Commit)
                     /         /
Remote Main:  A --- S (Squashed PR)
```
Resetting moves your local pointer from M back to S.

---

### 🎯 Outcome
* Local history is clean and linear.
* `git status` shows "Your branch is up to date".
* No unnecessary merge commits in your logs.

### 🧠 Key Takeaway

If `git pull` triggers a Vim window on your main branch, it usually means your local history has diverged.
`Reset --hard` is your best friend to get back in sync.

---

## 🔹 5. Warning: Deleting Branch "Not Yet Merged to HEAD"

### 🧠 Problem Summary

After a **Squash and Merge** on GitHub and updating your local `main`, you try to delete your local feature branch:

```bash
git branch -d feature/my-branch
```
You see a warning like:

```text
warning: deleting branch 'feature/my-branch' that has been merged to
         'refs/remotes/origin/feature/my-branch', but not yet merged to HEAD
```

---

### ❗ Root Cause
Because you used **Squash and Merge**, the commit IDs on your feature branch were replaced by a **single new commit ID**
on `main`.

Git looks at your local feature branch, compares its unique commit ID to `main`, and says: "H*ey, I don't see this
specific ID on main yet! Are you sure you want to delete it?*" It doesn't realize the **content** is already there under a different ID.

---

### 🚨 Symptoms

* A warning message during `git branch -d`.
* `git lg` shows your feature branch hanging off to the side, even though the work is already in `main`.

---

### 🔧 Solution (Clean Up)
### ✅ Use the Force (Carefully)
If you are 100% sure your PR was merged on GitHub, you can tell Git to delete the branch regardless of the ID mismatch:

```bash
git branch -D feature/my-branch
```
_(Note the capital -D—this force-deletes the branch)._


### ✅ Clean Up Remote Tracking
To stop seeing `origin/feature/my-branch` in your logs after deleting it on GitHub:

```bash
git fetch --prune
```
---

### 🧩 Mental Model

```text
Feature Branch:  [f42a92a]  <-- Git thinks this is "unmerged"
Main Branch:     [380efa8]  <-- This has the same CODE, but a different ID

```

### 🎯 Outcome

* Local branch list stays clean.
* No "ghost" branches remain in your git log.
* You understand that "Merged" in Git terms refers to Commit IDs, not just the code content.
---

### 🧠 Key Takeaway

**Squash and Merge** always changes commit IDs. Expect Git to be confused when you delete the local branch; using `-D `(capital D) is the standard way to handle this.

---

## 🔹 4. Merge Conflicts (Step-by-Step Resolution)

### 🧠 Problem Summary

When merging or rebasing branches:

```bash
git merge origin/main
# or
git rebase origin/main
```

Git may stop with a conflict:

```text
CONFLICT (content): Merge conflict in file.py
```

👉 Git cannot automatically decide how to combine changes.

---

### ❗ Why Conflicts Happen

Two branches modified the same part of a file:

```text
main branch        → changed line A
your branch        → also changed line A
```

👉 Git does not know which version to keep.

---

### 🚨 Symptoms

* Git stops the operation
* Files marked as **“both modified”**
* Conflict markers appear in files

---

## 🔍 What a Conflict Looks Like

Open the conflicted file:

```text
<<<<<<< HEAD
code from main branch
=======
your code changes
>>>>>>> feature-branch
```

---

### 🧩 Meaning of markers

* `<<<<<<< HEAD` → current branch (during merge)
* `=======` → separator
* `>>>>>>>` → incoming changes

⚠️ These markers must be removed manually.

---

## 🔧 Step-by-Step Resolution

### 1️⃣ Check status

```bash
git status
```

Identify conflicted files.

---

### 2️⃣ Open and fix the file

* Decide what to keep:

  * main version
  * your version
  * or combine both

* Remove ALL markers:

```text
<<<<<<<
=======
>>>>>>>
```

---

### 3️⃣ Mark as resolved

```bash
git add <file>
```

Or all files:

```bash
git add .
```

---

### 4️⃣ Continue the process

#### If using merge:

```bash
git commit
```

---

#### If using rebase:

```bash
git rebase --continue
```

---

## 🔁 Repeat if Needed

During rebase, conflicts may happen **multiple times** (per commit).

Repeat steps until complete.

---

## 🚑 Abort if Necessary

### Cancel merge:

```bash
git merge --abort
```

### Cancel rebase:

```bash
git rebase --abort
```

---

## ⚡ Quick Conflict Resolution Shortcuts

### Keep your version:

```bash
git checkout --ours <file>
```

### Keep incoming version:

```bash
git checkout --theirs <file>
```

Then:

```bash
git add <file>
```

---

### ⚠️ Important (Rebase vs Merge)

| Command | `--ours` means | `--theirs` means |
| ------- | -------------- | ---------------- |
| merge   | current branch | incoming branch  |
| rebase  | your commit    | main branch      |

👉 This difference is subtle but important.

---

## 🧠 Best Practices to Avoid Conflicts

* Sync frequently with `main`:

  ```bash
  git fetch origin
  git rebase origin/main
  ```

* Keep commits small and focused

* Avoid long-lived branches

---

## 🎯 Outcome

* Conflicts are resolved correctly
* History remains consistent
* Work continues safely

---

## 🧠 Key Takeaway

> Conflicts are normal — Git stops to let you decide. Fix the file, mark it resolved, and continue.

---


---
# 🔒 5. Protect `main` Branch (GitHub)

To ensure stability and prevent accidental changes, the `main` branch should be protected using GitHub branch protection rules.

### ⚙️ Steps

1. Go to your repository on GitHub
2. Navigate to **Settings**
3. Click on **Branches**
4. Add a new rule for:

   ```text
   main
   ```

---

### 📌 Recommended Settings

Enable the following options:

* ✅ **Require a pull request before merging**
  Ensures all changes go through a PR instead of direct commits.

* ✅ **Require approvals (at least 1)**
  Enforces code review before merging.

* ✅ **Dismiss stale pull request approvals**
  Prevents outdated approvals after new commits are pushed.

* ✅ **Require approval of the most recent push**
  Ensures the latest changes are reviewed.

* 🟡 **Require status checks (CI)** *(when available)*
  Blocks merging unless automated tests (e.g., pytest) pass.

* 🟡 **Require branches to be up to date before merging**
  Forces branches to sync with the latest `main` before merge.

* ✅ **Require conversation resolution before merging**
  Ensures all review comments are addressed.

* ❌ **Allow force pushes** → Disabled

* ❌ **Allow deletions** → Disabled

* 🔒 **Do not allow bypassing the above settings**
  Applies rules to all users, including administrators.

---

### 🎯 Outcome

With these protections in place:

* ❌ Direct commits to `main` are blocked
* ❌ Merging without review is prevented
* ❌ Outdated or untested code cannot be merged
* ✅ All changes follow a controlled PR workflow

---

### 🧠 Notes

* Some rules may require a **GitHub Pro/Team plan** or a **public repository** to be fully enforced.
* Status checks require CI integration (e.g., GitHub Actions).

---

##  ⚠️ PyCharm Warning for main

### Enable confirmation:
1. Go to Settings → Version Control → Git
2. Enable:
   - "Warn if committing to protected branch"

👉 Add `main` as protected branch

---

# 🤖 6. Continuous Integration (CI) with Pytest

To ensure code quality and prevent regressions, this project uses **automated testing with `pytest`** via GitHub Actions.

---

### ⚙️ What CI Does

On every **push** and **pull request**, the pipeline will:

* ✅ Install dependencies
* ✅ Run the full test suite using `pytest`
* ✅ Fail if any test fails
* ✅ Block merging into `main` (if branch protection is enabled)

---

### 📁 GitHub Actions Workflow

Create the following file:

```text
.github/workflows/tests.yml
```

---

### 🧾 Example Configuration

```yaml
name: Run Tests

on:
  push:
    branches:
      - main
      - "**"
  pull_request:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run pytest
        run: |
          pytest -v --maxfail=1 --disable-warnings
```

---

### 🔒 Integrating with Branch Protection

Once CI is set up:

1. Go to **Settings → Branches → Branch protection rules**
2. Enable:

   * ✅ **Require status checks to pass before merging**
3. Select the workflow check (e.g., `test`)

---

### 📊 Optional Enhancements

You can extend CI with:

* 📈 Coverage reporting:

  ```bash
  pytest --cov=src --cov-report=term-missing
  ```

* 🧹 Linting (recommended):

  ```bash
  pip install flake8
  flake8 .
  ```

* 🧪 Parallel execution:

  ```bash
  pip install pytest-xdist
  pytest -n auto
  ```

---

### 🧠 Notes

* Ensure `requirements.txt` includes all test dependencies (e.g., `pytest`, `requests`, etc.)
* Tests should be deterministic and not depend on external unstable services
* CI failures should always be fixed before merging

---

### 🎯 Outcome

With CI enabled:

* ❌ Broken tests cannot reach `main`
* ❌ Regressions are caught early
* ✅ Every PR is automatically validated
* ✅ Your API test framework remains stable and reliable

---

# 🔐 7. Secrets Management (API Keys for Tests)

Sensitive data such as API keys **must never be stored in the repository**.
Instead, use GitHub Actions **Secrets** to securely manage credentials.

---

### ⚙️ Why This Matters

* ❌ Prevents exposing credentials in code
* ✅ Keeps API keys secure
* ✅ Enables safe CI execution
* ✅ Follows best security practices

---

### 🔑 Step 1 — Add Secrets in GitHub

1. Go to your repository on GitHub
2. Navigate to **Settings → Secrets and variables → Actions**
3. Click **New repository secret**
4. Add your keys (example):

```text
WC_API_URL
WC_CONSUMER_KEY
WC_CONSUMER_SECRET
```

---

### 🧾 Step 2 — Use Secrets in GitHub Actions

Update your workflow:

```yaml
- name: Run pytest
  env:
    WC_API_URL: ${{ secrets.WC_API_URL }}
    WC_CONSUMER_KEY: ${{ secrets.WC_CONSUMER_KEY }}
    WC_CONSUMER_SECRET: ${{ secrets.WC_CONSUMER_SECRET }}
  run: |
    pytest -v --maxfail=1 --disable-warnings
```

---

### 🐍 Step 3 — Access Secrets in Python

Use environment variables in your code:

```python
import os

BASE_URL = os.getenv("WC_API_URL")
CONSUMER_KEY = os.getenv("WC_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("WC_CONSUMER_SECRET")
```

---

### 🧩 Recommended Pattern (for your framework)

Centralize configuration (e.g., `config.py`):

```python
from dataclasses import dataclass
import os

@dataclass
class Settings:
    base_url: str = os.getenv("WC_API_URL")
    consumer_key: str = os.getenv("WC_CONSUMER_KEY")
    consumer_secret: str = os.getenv("WC_CONSUMER_SECRET")

settings = Settings()
```

---

### 🧪 Local Development

For local testing, use a `.env` file (NOT committed):

```text
WC_API_URL=https://example.com
WC_CONSUMER_KEY=ck_xxx
WC_CONSUMER_SECRET=cs_xxx
```

Load it using:

```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
load_dotenv()
```

---

### 🚫 Important Rules

* ❌ Never commit `.env` files
* ❌ Never hardcode API keys
* ❌ Never print secrets in logs

---

### 🔒 Add to `.gitignore`

```text
.env
.env.*
```

---

### 🎯 Outcome

* 🔐 Secrets are securely stored
* 🔄 CI can run safely with real credentials
* 🧪 Local and CI environments are aligned
* ✅ Your test framework is production-ready


---

# 🧼 8. Clean Commit Strategy

## Rules:
- One logical change = one commit
- Write meaningful messages

### Format:
```
<type>: <short description>
```

### 🌳 Branch Naming Convention

- feature/... → new features
- fix/... → bug fixes
- refactor/... → refactoring
- test/... → test improvements

### Examples

```
refactor/request-utility-stateless
fix/customer-duplicate-validation
test/customers-negative-cases
```

## Avoid:
- "fix stuff"
- giant commits

---

# 🔍 9. Checking history and debugging

---

## I. 📜 Checking history

It provides a condensed, visual representation of your repository's recent commit history.

`git log --oneline --graph --decorate --all -10`

If you don’t want to enter the pager:

`git --no-pager log --oneline --graph --decorate --all -10`

Here is a breakdown of what each part of the command does:

* `--oneline:` Each commit is condensed into a single line that includes a shortened version of the commit hash and the first line of the commit message.
* `--decorate:` Displays the names of branches, tags, and HEAD next to the commits they currently point to.
* `--graph:` Adds a text-based ASCII graph (using symbols like *, |, and /) on the left side of the output to visualize branching and merging.
* `-10`: Limits the output to only the 10 most recent commits in the history.

---

### 🔎 See the actual code changes in each commit:

```
git log -p
```
---

### 🔎 To see what was added but NOT yet committed:
```
git status
```

---

### 🔎  See the actual code changes you staged (after running `git add .`):
```
git diff --cached
```

---

### 🔎  To see your "Internal" history `git reflog`:
`git reflog` is your local "undo history" for Git. While git log shows the commit history of a branch, `git reflog `
`records every time your HEAD moves`—including actions that don't usually appear in your history, like switching
branches, rebasing, or performing a hard reset.


### 🔑 Key Features

* T**he Safety Net**: It allows you to find and recover "lost" commits that are no longer reachable by any branch, such as those deleted during a git reset --hard.
* **Local Only**: This log is stored strictly on your machine. It is not pushed to remote servers like GitHub, so your teammates cannot see your local "reflog".
* **Temporary:** By default, Git keeps these records for 90 days before automatically pruning them to save space.

### ⚙️ How to Use It for Recovery
If you accidentally deleted work with a hard reset, follow these steps to get it back:

1. **Run the command:**
```bash
git reflog
```

2. **Find the state you want:**

    Look through the list for the last "good" state before your mistake. It will look like `HEAD@{n}` (e.g., `HEAD@{2}`
    was where you were two moves ago).


3. **Restore it**:

    Use a hard reset to jump back to that specific moment:

    `git reset --hard HEAD@{n}`

### ⚖️ Comparison: Reflog vs. Log

| Feature | `git log` | `git reflog` |
| :--- | :--- | :--- |
| **Focus** | Public commit history of the branch. | Private, chronological log of all HEAD moves. |
| **Visible Actions** | Standard commits and merges. | Resets, checkouts, rebases, and amends. |
| **Visibility** | Shared when you push/pull. | Stays only on your local computer. |


---

### 🔎 Show commits on the feature branch:

```Bash
git log feature/GitHub_CI --oneline
```

---

### 🔎 Show only commits DIFFERENT from main (most useful):
This is usually what you actually want:
```Bash
git log main..feature/GitHub_CI --oneline
```
👉 Meaning:
>“Show commits that are in feature/GitHub_CI but NOT in main”

---

### ⚖️ Compare both branches directly
What feature branch has that main doesn’t:
```
git log main..feature/GitHub_CI --oneline
```

What main has that feature branch doesn’t:
```
git log feature/GitHub_CI..main --oneline
```
---

### 📊 See actual code differences too

```
git diff main..feature/GitHub_CI
```

Or just filenames:
```
git diff --name-only main..feature/GitHub_CI
```
---

### 🔎   To see changes compared to main:

Since you just did a git fetch, you might want to see how your feature branch differs from the server's main:

```Bash
git diff main..HEAD
```
👉 Shows what you have added that isn't in main yet.

---
## II. 🐞 Debugging Git

---

### ♻️ Git reset:

In Git, `reset` is the command used to move the HEAD (your current location) to a specific previous commit.
The flags `--soft `and `--hard `determine what happens to the work you've done since that commit.
Think of it as choosing how much of your "undo" you want to keep.

### 1. `git reset --soft `(The "Safety" Undo)

This moves HEAD back to a previous commit but keeps all your changes.

* **What happens:** The commits disappear from the history, but your work stays exactly as it is in your "Staging Area" (ready to be committed again).
* **When to use it:** You made a commit but realized you forgot to add a file or want to rewrite the commit message.
* **Result:** Your files don't change; you just get a "do-over" on the commit itself.

### 2. `git reset --hard` (The "Nuclear" Undo)

This moves HEAD back and destroys all changes made after that point.

* **What happens**: Both the commits and your uncommitted file changes are deleted. Your project will look exactly like it did at that specific point in the past.
* **When to use it:** You’ve made a mess of your code, nothing works, and you want to completely wipe the slate clean and start over from a known good state.
* **Danger:** You cannot easily undo a --hard reset. Any unsaved work is gone forever.


| Flag | Moves HEAD? | Keeps Changes in Files? | Keeps Changes Staged? |
| :--- | :--- | :--- | :--- |
| **--soft** | Yes | Yes | Yes |
| **--mixed** (Default) | Yes | Yes | No (Unstaged) |
| **--hard** | Yes | No (Deleted) | No (Deleted) |

---

### ✂️ Git bisect:

`git reflog` is for finding your own mistakes, but `git bisect` is for finding **bugs** introduced by others (or yourself) in the past.

It uses a **binary search** algorithm to quickly find the specific commit that broke your code. Instead of checking
100 commits one by one, `git bisect` can find the "bad" commit in about 7 steps.


How to use it
Think of it like a game of "Higher or Lower":

1. **Start the process**:
```
git bisect start
```
2. **Mark the current state as broken**:
```
git bisect bad
```
3. **Find a point in the past where the code worked**:
`git bisect good <commit-hash> `(e.g., from two weeks ago).
4. **The Test**: Git will automatically jump to a commit in the middle. You test your code (run your app or a script).

    * If it works: Type `git bisect good`
    * If it's broken: Type `git bisect bad`

5. **Repeat**: Git keeps splitting the remaining commits in half until it points to the exact "first bad commit."
6. **Finish**: Once you've found the bug, return to your original branch:
git bisect reset

### 🤖 Automation:
If you have a test script (e.g., `npm test` or `python test.py`), you can automate the whole thing:
```
git bisect run ./test_script.sh`
```

Git will run the script at every step and find the bug for you while you grab a coffee.

### ⚖️ Comparison: Bisect vs. Blame

| Feature | `git blame` | `git bisect` |
| :--- | :--- | :--- |
| **Goal** | Shows who wrote a specific line. | Finds which commit broke the logic. |
| **Best For** | Finding the author of a line. | Finding "silent" bugs in complex code. |
| **Effort** | Instant. | Requires manual or scripted testing. |


---



# ⚡ 10. Git Shortcuts logs and prune

Git aliases are custom shortcuts used to simplify frequently typed Git commands. They allow you to define a shorter
name for a longer command, such as typing git co instead of git checkout, which saves time and reduces typing errors.

---

## 🔹1. 🗃️ Set shortcut for logs (set, edit, delete):

```
git config --global alias.lg "log --oneline --graph --decorate --all -10"
```

📝 _Note: You don't need --no-pager inside the Git alias because Git aliases automatically handle the output correctly,
but you can add it if you strictly want to bypass the pager._

### 🔥 Now you only run shortcut:

```
git lg
```
---


## 🔹 2. 🗃️ Set shortcut for prune

Run this command to save the shortcut globally:

```
git config --global alias.fp "fetch origin --prune"
```
## 💡 Why this is useful:
Over time, your local Git history gets cluttered with "ghost" branches that have already been deleted on GitHub. Running git fp will:

* Update your local list of remote branches.
* Remove any remote-tracking references (like origin/old-feature) that no longer exist on the server.
* Keep your `git lg `graph much cleaner by hiding branches that are finished.

✨ **Pro Tip:** You can actually tell Git to always prune whenever you fetch or pull by running:
`git config --global fetch.prune true`. This way, you don't even need a shortcut!
---


## ✏️ Edit the shortcut

### 1. Overwrite it via Command Line
Simply run the `git config `command again with the **new** definition. Git will automatically overwrite the old `lg` alias
with whatever you type last:

```
git config --global alias.lg "log --oneline --graph --decorate --all -20"
```
_(In this example, I changed -10 to -20 to show more commits)._

### 2. Edit the Git Config File (Recommended)
If the command is getting long and you want to see exactly what you've saved, it's often easier to edit your global
config file directly:

```
git config --global --edit"
```

Look for the `[alias] `section. It will look like this:

```
[alias]
    lg = log --oneline --graph --decorate --all -10
```
_Modify the text after the = sign, save the file, and close it. The changes take effect immediately._

---

## 🗑️ How to Delete an Alias
If you want to start over or remove it entirely:

```
git config --global --unset alias.lg
```

---

# 🔀 11. Rebase vs Merge `main` branch

Merging/rebasing `main` into your current branch (like a "fix" or "feature" branch) is a best practice used to detect
and resolve conflicts early before your code ever reaches the shared repository.
---

### 💡 Why merging/rebasing is the "Best Practice before pushing your code?"

* **Conflict Resolution:** It allows you to deal with any overlapping changes made by teammates while you are still in your own safe space. It is much better to fix a conflict locally on your branch than to break the shared main branch or a Pull Request.
* **Testing against the "Future"**: By merging/rebasing main, you are testing your changes against the most up-to-date version of the project. This ensures your fix still works with new code others have added.
* **Cleaner Pull Requests**: Most platforms like GitHub or GitLab will not let you merge a Pull Request if it has conflicts with the target branch. Updating your branch first makes the final merge into main a "clean" one.

### 👉 Here is the "Why" in a real-world scenario:

1. **Monday**: You start your fix branch. main is at Version A.
2. **Tuesday**: You are still working. A teammate merges a big change into main. main is now at Version B.
3. **Wednesday**: You finish. If you try to merge your code (based on Version A) into main (which is now Version B), GitHub might get confused or show a Merge Conflict.

### ✅ By doing this step:

* You bring Version B into your fix branch locally.
* If your teammate's new code breaks your fix, you see it immediately on your computer.
* You fix it, test it, and then push.
* When you finally open the PR, GitHub sees that your branch already "knows" about Version B. The merge button turns green, and everything is smooth.

### ✨ The Golden Rule:
Always merge/rebase main into your branch before you merge your branch into main. It keeps the "drama" on your local
machine and keeps the shared main branch clean and working.

## Rebase (clean history)

```bash
git pull --rebase origin main
```

✔ Linear history
✔ Cleaner logs
❌ Requires care

An example of `git rebase origin/main` is standard best practice—as long as you are currently sitting on your private
feature branch when you run it.

### ✅ 1. The Good Practice (Updating your branch)
If you are on `bug/ticket_fix_1234` and run:

```
bash

git fetch origin
git rebase origin/main
```

This is great. You are taking your private, unmerged commits and "lifting" them to sit on top of the latest work from
the team.

**Why:** It keeps your history clean and ensures your code works with the very latest version of the project before you
submit a Pull Request.

### ❌ 2. The Bad Practice (Rebasing Main itself)
If you are on the main branch and run:

```
bash

git checkout main
git rebase some-other-feature  # BAD
# OR
git rebase (any command that changes existing main commits) # BAD
```

This is the "never do this" zone. If you rewrite the history of main and then git push --force, you break the repository
for everyone else on the team. Their local main will no longer match the server, and they’ll get "diverged branch" errors.

## Merge (default)

`git merge` is the command used to combine the history and changes from one branch into another

```bash
git merge main
```

* ✔ Keeps full history
* ❌ Creates extra merge commits

---


## When to use what?

| Situation | Use |
|----------|-----|
| Team/shared branch | Merge |
| Personal feature branch | Rebase |


### 🏷️ Summary: Where are you standing?
The "**safety**" of a rebase depends entirely on which branch you are currently on:

- **On your private branch?** Rebase away! It’s your sandbox. It makes your eventual Pull Request look professional and easy
to review.

- **On a shared/production branch**? Stick to git merge or git pull. Never rewrite history that others are counting on.


## ⚡ Recommended for YOU

Since you:
- work solo or small team
- do incremental refactoring

👉 Use:
```
git pull --rebase origin main
```


### The Breakdown

`git pull --rebase origin main` is simply a shortcut (an "alias" of sorts) for running those two commands manually.

| Step | `git fetch` + `git rebase` | `git pull --rebase` |
| :--- | :--- | :--- |
| **Step 1** | `git fetch origin` (Downloads new data) | Done automatically in the background. |
| **Step 2** | `git rebase origin/main` (Moves your commits) | Done automatically in the background. |

### 🧠 Why use one over the other?
**1. Use the two-step (fetch then rebase) if:**

- **You're cautious:** You want to run git log origin/main after fetching to see what your teammates actually changed
before you commit to rebasing your work on top of it.
- **You're debugging:** If a rebase goes wrong, it's sometimes easier to see exactly where it failed when running the
commands individually.

**2. Use the one-liner (pull --rebase) if:**

- **You're in a flow:** You trust the incoming changes and just want to sync up as fast as possible.
- **You hate "Merge" commits:** You want to avoid that "Merge branch 'main' of..." commit message that a standard git pull creates.

`git pull --rebase origin main` is a pro move for keeping your local work clean. It’s a shortcut that does two
things in one command:

1. **Fetch:** Grabs the latest commits from the remote main.
2. **Rebase:** Takes your local, unpushed commits and "lifts" them to sit on top of those new incoming commits.

## 🧠 Why people love it:
Without `--rebase`, a standard `git pull` performs a merge. This often creates a "clutter" commit that says something
like "Merge branch 'main' of github.com..." every time you sync.

Using -`-rebase` avoids that extra commit, keeping your branch history a perfectly straight line.

## 🧪 The Bottom Line:
As long as you are standing on your private feature branch, `git pull --rebase` is the cleanest way to stay up to date.

---
# 12. 🍒 Command `git cherry-pick`

`git cherry-pick `is a command that allows you to select specific, individual commits from one branch and apply them to another.

Unlike `git merge `or `git rebase`, which integrate entire branch histories, cherry-picking gives you "surgical precision"
to move only the exact changes you need.

### 🧠 How It Works
When you cherry-pick a commit, Git calculates the changes (diff) introduced by that commit and applies them to your
current working branch.

* **New Commit**: It creates a new commit object on your target branch with a unique SHA identifier, even if the content is
identical to the original.
* **Original Unchanged**: The original commit remains exactly where it was in its source branch.

### 📝 Common Use Cases

* **Hotfixes**: If you find a critical bug in a feature branch but aren't ready to merge the whole feature yet, you can cherry-pick just the fix commit into your production branch.
* **Undo/Correct Mistakes**: If you accidentally committed code to the wrong branch, you can cherry-pick it onto the correct one and then revert it on the original.
* **Backporting**: Bringing specific features or bug fixes from a newer version of the software (e.g., main) back to an older, supported release branch.

---

# 🔀 13. Switching Branches

### Modern way

```bash
git switch main
git switch QA_bug_4567
```

### Classic way

```bash
git checkout main
```

### Quick toggle

```bash
git switch -
```

---

# 14. 🔗 Upstream Branch (Tracking)

Set upstream manually:

```bash
git branch --set-upstream-to=origin/main
```

Check tracking:

```bash
git branch -vv
```

Lists all the remote repositories:

It checks currently connected repositories to your local project, along with their specific URLs

```bash
`git remote -v`
```

List only remote branches:

```
git branch -a
```

List everything:

```
git branch -r
```

---

## 🛠 Troubleshooting

### Error:
```
fatal: The current branch has no upstream branch
```
That error just means your local main branch is "homeless"—it doesn't know which remote (GitLab or GitHub) should be
its default partner.

### Fix:

```bash
git push -u origin branch-name
# or
git push --set-upstream origin branch-name
```

 To have this happen automatically for branches without a tracking upstream, see '`push.autoSetupRemote`'
 in 'git help config'`

_Note: -u is shorthand for --set-upstream. Once you do this once, you can just type git push in the future and it will
remember your choice.)_
---

# 15. 🤖 Automating of the creation and tracking of remote branches

If you want Git to automatically set up this "partnership" every time you create a new branch in the future,
enable automatic upstream setup:

```bash
git config --global push.autoSetupRemote true
```
### 🧼 How it works:

**The Problem:**

Normally, when you create a new local branch and try to run git push, Git stops you because it doesn't know where on
the server to put it. You are forced to type `git push --set-upstream origin your-branch-name`.

**The Fix:**

With this setting enabled, you can just type git push. Git will automatically:
Create a branch with the same name on your remote (like GitHub or GitLab).
Set up "tracking," meaning your local branch is now officially "linked" to that remote version.
Breaking down the command:

- `git config`: Accesses your Git settings.
- `--global`: Applies this change to every repository on your computer, not just the current one.
- `push.autoSetupRemote true`: Enables the specific feature that assumes --set-upstream on your behalf.

---
# 🧪 16. Automatically normalizing line endings

There are times that you can these warnings:

```
$ git add . warning: in the working copy of '.gitattributes', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/README_GIT_GITLAB_SETUP_GUIDE.md', CRLF will be replaced by LF the next time Git
touches it warning: in the working copy of 'docs/README_GIT_WORKFLOW_HANDBOOK.md', CRLF will be replaced by LF the next
time Git touches it.
```
These warnings are Git's way of telling you it is
automatically normalizing line endings to ensure they are consistent across different operating systems.

The best practice for modern development—especially in teams—is to use a
`.gitattributes` file.

While `git config --global core.autocrlf true` was a standard recommendation for years, it has major drawbacks
compared to the file-based approach.

### 🧠 Why `.gitattributes `is better

 - **Version Controlled:** The file is part of your repository, so every developer—regardless of their OS or personal Git settings—automatically uses the same rules.
 - **Overwrites Local Config:** Rules set in .gitattributes take precedence over any individual's core.autocrlf setting, preventing "phantom changes" where a file looks modified but has no text changes.
 - **Granular Control:** You can specify exact behavior for different file types (e.g., forcing LF for shell scripts while letting images remain binary).

### 📌 When to use `core.autocrlf true`
This setting is now primarily a **personal preference** or a **fallback** for projects that lack a `.gitattributes` file.

 - **Use it if**: You are a Windows developer working on many different projects that don't have their own line-ending policies.
 - **Avoid it if**: You are working in a professional team; you should insist on a `.gitattributes` file to ensure the repo stays
clean for everyone.

### 🔍 How to verify your current config

```
git config --global core.autocrlf
```

**Output:**
* true → conversion enabled
* false → disabled
* empty → not set

If the outcome is `true` and you have the file `.gitattributes` created, then change it to `false`:
```
git config --global core.autocrlf false
```

### 🔥 Important: After changing it

If you switch to `false`, do one cleanup:

```
git add --renormalize .
git commit -m "chore: normalize after disabling autocrlf"
```

### 🧠 What `git add --renormalize .` actually does

👉 It tells Git:

“Re-check all files and apply `.gitattributes `rules again”

Git says:
`"this file should be LF → I’ll fix and stage it"`

### ✅ When you SHOULD use it
1️⃣ After adding `.gitattributes`


2️⃣ After changing line-ending rules

Example:

`*.md → now LF instead of auto`

3️⃣ When fixing mixed line endings

Example:

`w/mixed`


### 📁 Check File Status: Run: `git ls-files --eol`

To see exactly which line endings are currently in your index (i/) and your working tree (w/).



### 🚀 Summary of Best Practice


| Feature | .gitattributes (Recommended) | core.autocrlf |
| :--- | :--- | :--- |
| **Scope** | Repository-wide | Local machine only |
| **Consistency** | Guaranteed for all team members | Depends on everyone's setup |
| **Precision** | Target specific extensions | Applies to everything |
| **Safety** | Prevents binary file corruption | Risk of corrupting binaries |

---

# 17. 📚 Configuration file  .pre-commit-config.yaml

`.pre-commit-config.yaml` is the configuration file for pre-commit, a framework used to manage and maintain multi-language Git hooks.

Placed at the root of a repository, this file tells the tool which automated checks (hooks) to run every time you
attempt a `git commit`. If any of these checks fail, the commit is blocked, ensuring that only high-quality, formatted
code enters your repository.

### 🧠 Here is how high-level teams typically handle it:

### 1. "Shift Left" (Local Enforcement)
Companies want to catch bugs before they reach the server.

* **Onboarding:** When a new dev joins, they run pre-commit install. This hooks into their local Git.

* **Automatic Checks:** Every time they run git commit, the hooks run. If a file has trailing whitespace or fails a test, the
commit is blocked locally. This saves time and CI (Continuous Integration) costs.

### 2. CI/CD Gatekeeper (The "Safety Net")
Even if a developer skips the local check (using --no-verify), the CI pipeline (GitHub Actions, GitLab CI, or Jenkins)
runs the exact same checks.

* The pipeline runs `pre-commit run --all-files` or `pre-commit run`.
* If it fails, the **Merge Request (MR)** or **Pull Request (PR)** is blocked. You cannot merge broken or poorly formatted code.

```
pre-commit run  # staged files only
pre-commit run --all-files  # entire repo
```

### 3. Centralized Shared Configs
In very large companies (hundreds of repos), they don't copy-paste the config.

* They create a "**Global Pre-commit Repo**".
* Individual projects then reference those "central" hooks so that every project in the company follows the same
Python/Black/Linting standards automatically.


### 🔄 Key Functions

- **Defining Hooks**: It lists the external repositories and specific "hook IDs" to be used, such as Black for Python formatting or Prettier for web technologies.
- **Version Control**: It specifies the exact version (rev) of each tool to use, ensuring that every developer on a team runs the exact same checks.
- **Customization**: You can configure global settings like exclude patterns to skip specific files or default_stages to define when hooks should run (e.g., only on commit or also on push).

### 📌 Basic Workflow

1. **Install the tool:** Run pip install pre-commit.
2. **Create the file**: Add `.pre-commit-config.yaml `to your project root.
3. **Set up Git**: Run `pre-commit install `to link the configuration to your local `.git/hooks` folder.
4. **Commit**: When you run git commit, the hooks run automatically. If you need to skip them for a specific commit, use `git commit --no-verify`

### ⚠️ After updating `pre-commit-config.yaml` one important thing to expect:

```
pre-commit install
pre-commit run --all-files
```
👉 It will:

* fix files
* maybe fail once
* then pass on next commit

 What big teams do is NOT a raw `.git/hooks/pre-commit` script — they use a managed tool (e.g. file: `.pre-commit-config.yaml`) so it’s:
 - versioned in the repo
 - consistent for everyone
 - easy to maintain

 ✅ Use the pre-commit framework (Python tool `.pre-commit-config.yaml`) 👉 This replaces manual `.git/hooks/pre-commit`

 🔥 Why this is MUCH better than .git sample hook current script.

 | Feature         | Script       | Enterprise setup |
| --------------- |--------------| ---------------- |
| Whitespace fix  | ❌ warn only  | ✅ auto-fix       |
| Formatting      | ❌ none       | ✅ black          |
| Linting         | ❌ none       | ✅ flake8         |
| Test control    | ❌ all tests  | ✅ smoke only     |
| Team sharing    | ❌ local only | ✅ repo-wide      |
| Maintainability | ❌ manual     | ✅ config-driven  |


### ⚠️ TROUBLESHOOTING:
One important real-world note.

### 1. Black sometimes:

`Black modifies files → commit fails`

👉 You just:

```
git add .
git commit
```

**Second attempt → passes**


### 2. Stage the changes

You need to stage the modified files and attempt the commit again.

1. Stage the changes: The hook has already "fixed" the files for you, but those fixes are now unstaged.
Run: `git add .`

2. Commit again: Run your original commit command. This time, the hook should pass because the trailing whitespace is gone.
```
[INFO] Stashing unstaged files to C:\Users\kwaki\.cache\pre-commit\patch1774432283-1224.
trim trailing whitespace.................................................Failed
- hook id: trailing-whitespace
- exit code: 1
- files were modified by this hook
```

---

# 17. 🔍 Git Fetch vs. Git Pull
In Git, `git fetch` is a "safe" command that downloads the latest changes (commits, files, and branches) from a remote repository
(like GitHub) to your local machine without merging them into your actual work.

Think of `git fetch` as checking the mail and git pull as opening the mail and acting on it.


When you run `git fetch origin`, Git downloads updates for all branches on that remote. This updates your local
"remote-tracking branches" (like `origin/main`, `origin/develop`, etc.) to match what’s on the server.

### 💡 When to use `git fetch origin main`:
While not strictly necessary for general syncing, adding main changes the behavior in specific ways:

* Speed/Size: It limits the fetch to only that one branch. This is useful if the repository is massive and you only care about seeing updates to main


### 1. 🛡️ The "Safety First" Approach

- Scenario: You know your teammate pushed code, but you're worried it might break your current work.
- Command: `git fetch`
- Result: You can now see their new commits in your history (via git log), but your code files don't change.
You are safe to keep working.

### 2. 🔄 The "Update Me Now" Approach

- **Scenario**: You just sat down to work and want your local files to match exactly what is on GitHub right now.
- **Command**: `git pull`
- **Result**: Git downloads the data and updates your files immediately. If there are conflicts, you'll have to fix them right now.

### 3. ⚖️ The "Comparison" Approach

- **Scenario**: You want to see exactly how many commits you are "behind" the rest of the team.
- **Commands**:
    ```
    git fetch (Updates your local records)
    git status

    # or this actually shows what’s new
    git log HEAD..origin/main --oneline

  ```
- Result: Git will tell you: "Your branch is behind 'origin/main' by 3 commits." No files were moved or changed in the process.


| Command | What it does | Impact on your code |
| :--- | :--- | :--- |
| **git fetch** | Downloads data from remote | **None.** Only updates remote tracking. |
| **git pull** | `git fetch` + `git merge` | **Updates your local files** immediately. |

In Git, `git pull` is essentially a combination of `git fetch` followed immediately by `git merge`. By breaking these apart, you gain more control:

* `git fetch origin main`: Specifically downloads the latest history from the `main` branch on the server (`origin`) and
stores it in your local remote-tracking branch, usually named `origin/main`.
* `git merge origin/main`: Integrates those specific downloaded changes into your current branch (e.g., `fix/bug_ticket_1235`)
without ever needing to touch your local `main` branch.



---

# 🎯 Key Takeaways

- Always start from updated main
- Use PRs for everything
- Prefer rebase for clean history
- Protect main branch
- Keep commits clean and small
- Use PyCharm UI for simplicity
