# Git Workflow Guide for QA Engineers (Advanced)

---

# 🚀 Overview
This guide expands the standard Git workflow with:
- Dual GitHub + GitLab setup
- PyCharm-only workflow
- Branch protection
- Commit strategy
- Merge conflict avoidance
- Rebase vs Merge

---

# 🔁 Standard Workflow

```
main → create branch → commit → push → PR → merge → delete branch
```

---

# 🌐 1. Dual GitLab + GitHub Workflow

## Setup "both" remote

```bash
git remote add both <GitLab-URL>
git remote set-url --add --push both <GitHub-URL>
git remote set-url --add --push both <GitLab-URL>
```

## Push to both

```bash
git push both
```

## PyCharm alternative
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

## ✅ Step-by-Step CLI Workflow Guide

### 1. Always start from updated main

```bash
git checkout main
git pull origin main
```

👉 Mandatory before starting new work

---

### 2. Create a new branch

```bash
git checkout -b QA_bug_4567
```

---

### 3. Work on your code

Make changes in PyCharm.

---

### 4. Stage changes

```bash
git add .
```

---

### 5. Commit changes

```bash
git commit -m "Fix: login flow bug"
```

---

### 6. Push branch

```bash
git push -u origin QA_bug_4567
```

---

### 7. Create Pull Request (PR)

- Go to GitHub
- Click "Compare & pull request"
- Add description
- Submit PR

---

### 8. Merge PR

- Use "Squash and merge" (recommended)
- Ensures clean commit history

---

### 9. Cleanup (Delete branch)

#### Delete remote branch (GitHub)
- Click "Delete branch"

OR

```bash
git push origin --delete QA_bug_4567
```

#### Delete local branch

```bash
git checkout main
git pull origin main
git branch -d QA_bug_4567
```

---

## 🔄 Optional: Clean stale branches

```bash
git fetch origin --prune
```

👉 Removes deleted remote branches from local references
👉 Not required, but good for cleanup

---

## ⚠️ Important Notes

- `git branch -d` → safe delete (only if merged)
- `git branch -D` → force delete (use carefully)

- `-u` flag in push:
```bash
git push -u origin branch-name
```
Links local and remote branch for future pushes

---


# 🔒 3. Protect main branch (GitHub)

## Steps:
1. Go to repository → Settings
2. Click **Branches**
3. Add rule for `main`

## Recommended settings:
- Require pull request before merging
- Require status checks (CI)
- Require branches to be up to date
- Restrict direct pushes

👉 Prevents accidental commits to main

---

# ⚠️ PyCharm Warning for main

## Enable confirmation:
1. Go to Settings → Version Control → Git
2. Enable:
   - "Warn if committing to protected branch"

👉 Add `main` as protected branch

---

# 🧼 4. Clean Commit Strategy

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

# 🧠 5. How to Avoid Merge Conflicts

## Golden Rule:
Always branch from updated main

```bash
git checkout main
git pull origin main
git checkout -b new-branch
```

## Keep branches:
- small
- short-lived


## Sync frequently:
```bash
git pull --rebase origin main
```

👉 Reduces conflicts dramatically

---

# 🔀 6. Rebase vs Merge

## Merge (default)

```bash
git merge main
```

✔ Keeps full history
❌ Creates extra merge commits

---

## Rebase (clean history)

```bash
git pull --rebase origin main
```

✔ Linear history
✔ Cleaner logs
❌ Requires care

---

## When to use what?

| Situation | Use |
|----------|-----|
| Team/shared branch | Merge |
| Personal feature branch | Rebase |

---

# ⚡ Recommended for YOU

Since you:
- work solo or small team
- do incremental refactoring

👉 Use:
```
git pull --rebase origin main
```



---


# 🔥 Final Professional Workflow

```
[After merge]
↓
Delete branch (remote + local)
↓
Checkout main
↓
Pull latest changes
↓
(Optional) git fetch --prune
↓
Create new branch
↓
Work + commit
↓
Push
↓
Create PR
↓
Merge
↓
Repeat
```


---


---

## 🔀 Switching Branches

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

## 🔗 Upstream Branch (Tracking)

Set upstream manually:

```bash
git branch --set-upstream-to=origin/main
```

Check tracking:

```bash
git branch -vv
```

Lists all the remote repositories:
```bash
`git remote -v`
```
It checks currently connected repositories to your local project, along with their specific URLs

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

## ⚡ Pro Tip

If you want Git to automatically set up this "partnership" every time you create a new branch in the future,
enable automatic upstream setup:

```bash
git config --global push.autoSetupRemote true
```
### 🧼 How it works:

**The Problem:**

Normally, when you create a new local branch and try to run git push, Git stops you because it doesn't know where on
the server to put it. You are forced to type git push --set-upstream origin your-branch-name.

**The Fix:**

With this setting enabled, you can just type git push. Git will automatically:
Create a branch with the same name on your remote (like GitHub or GitLab).
Set up "tracking," meaning your local branch is now officially "linked" to that remote version.
Breaking down the command:

- `git config`: Accesses your Git settings.
- `--global`: Applies this change to every repository on your computer, not just the current one.
- `push.autoSetupRemote true`: Enables the specific feature that assumes --set-upstream on your behalf.

---


## 📌 Summary

You only delete the branch **after merge**.

Deleting earlier = losing your work.



# 🎯 Key Takeaways

- Always start from updated main
- Use PRs for everything
- Prefer rebase for clean history
- Protect main branch
- Keep commits clean and small
- Use PyCharm UI for simplicity
