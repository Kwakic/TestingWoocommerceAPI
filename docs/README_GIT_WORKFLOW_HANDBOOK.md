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

**Note**: Use one branch per ticket/feature if all commits belong to the same ticket/feature.

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
## 🧪 Automatically normalizing line endings

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

## 📚 Configuration file  .pre-commit-config.yaml

`.pre-commit-config.yaml` is the configuration file for pre-commit, a framework used to manage and maintain multi-language Git hooks.

Placed at the root of a repository, this file tells the tool which automated checks (hooks) to run every time you
attempt a git commit. If any of these checks fail, the commit is blocked, ensuring that only high-quality, formatted
code enters your repository.

### 🧠 Key Functions

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
*
 What big teams do is NOT a raw `.git/hooks/pre-commit` script — they use a managed tool so it’s:
 - versioned in the repo
 - consistent for everyone
 - easy to maintain

 ✅ Use the pre-commit framework (Python tool) 👉 This replaces manual `.git/hooks/pre-commit`

 🔥 Why this is MUCH better than .git sample hook current script.

 | Feature         | Your script  | Enterprise setup |
| --------------- | ------------ | ---------------- |
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

## 🔍 Git Fetch vs. Git Pull

| Command | What it does | Impact on your code |
| :--- | :--- | :--- |
| **git fetch** | Downloads data from remote | **None.** Only updates remote tracking. |
| **git pull** | `git fetch` + `git merge` | **Updates your local files** immediately. |


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
