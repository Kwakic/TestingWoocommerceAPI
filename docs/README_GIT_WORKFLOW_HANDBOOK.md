# Git Workflow Guide for QA Engineers (Advanced)

---

# 🚀 Overview
This guide expands the standard Git workflow with:
- Changing Remotes, Dual GitHub + GitLab setup
- PyCharm + CLI workflow
- Branch protection
- Commit strategy
- Merge conflict avoidance
- Rebase vs Merge

---

# 🔁 Standard Workflow

```
main → create branch → work on code → commit → push → PR → merge → delete branch
```

---

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

# 🧑‍💻 2.a. PyCharm-Only Workflow (No Terminal)

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
# 🧑‍💻 2.b. Step-by-Step CLI Workflow Guide (Terminal)



## 🔹Step 1 — ✅ Always start from updated main

```bash
git checkout main
git pull origin main

# If you receive a message: There is no tracking information for the current branch.
# Git doesn't know: which remote? which branch? Run following command to set it:
git branch --set-upstream-to=origin/main
# or a shortcut:
git branch -u origin/main
# You usually only need to run `git branch -u origin/main` once per machine. After that, a simple git pull is enough.
```

❗Mandatory before starting new work. This gets your local main up to speed with the server in one go.

---

## 🔹Step 2 —  🛠️ Create a new branch (in case you don't have any)

**Note**: Use one branch per ticket/feature if all commits belong to the same ticket/feature.

```bash
git checkout -b fix/bug_ticket_1235
```

---

## 🔹 Step 3 — 👩🏻‍💻 Work on code

Make changes in code/file in PyCharm.

---

## 🔹 Step 4 —  📝 Stage and commit changes before merging it

Before you do next step (the merges: `git merge main` to avoid possible conflict when we push our code from fixing branch),
your "Working Directory" must be clean.

Git protects your work by blocking any merge that might overwrite your uncommitted changes. If you have half-finished
code that isn't ready to commit, Git will block the merge.



You have two choices before you merge main into your branch:

### 1️⃣ The "Commit" way:

If your code is "good enough," move changes from your working directory to the staging area:

```bash
git add .
```

If you own `.pre-commit-config.yaml` file the best practice is to run `pre-commit run --all-files` before to run
`git commit -m "....."`

#### Why to run it?

* Run pre-commit before committing to **catch and fix issues early**
* **Automatic Fixing**: If a hook (like a code formatter) modifies your files, those new changes will be unstaged. You will
need to git add them again before you can successfully commit.
* **Manual verification**: Running it manually after git add lets you catch and fix errors before entering the commit message interface.

```bash
# This runs only on staged files (what you just added)
pre-commit run
```

Now run the commit:

```bash
git commit -m "WIP: working on login"
```
Now your directory is clean.

---

### 2️⃣ The "Stash" way:

Use git stash when your changes are not ready to commit.

#### ✅ Why this is better than committing?

* Keeps history clean (no cluttering your history): You don't have to make messy commits like "saving progress" or
"work-in-progress" etc. just to get a merge to work.

* If your code is a mess and you don't want to commit it yet, the standard "Git Pro" move is to use `git stash`.
It’s like a temporary drawer for your work (pause).

This allows you to pull in updates from main even if you have half-finished code sitting in your fix branch.

Stash your work. Move your uncommitted changes to a temporary storage area by running following command:

```
git stash
```

💡 _Your half-finished changes disappear; the directory is now "clean"_

---


## 🔹 Step 5 — 🔄 Merge possible changes from the main branch into your fix branch.

Merging `main` into your current branch (like a "fix" or "feature" branch) is a best practice used to detect and resolve
conflicts early before your code ever reaches the shared repository.

### 💡 Why merging is the "Best Practice"

* **Conflict Resolution:** It allows you to deal with any overlapping changes made by teammates while you are still in your own safe space. It is much better to fix a conflict locally on your branch than to break the shared main branch or a Pull Request.
* **Testing against the "Future"**: By merging main, you are testing your changes against the most up-to-date version of the project. This ensures your fix still works with new code others have added.
* **Cleaner Pull Requests**: Most platforms like GitHub or GitLab will not let you merge a Pull Request if it has conflicts with the target branch. Updating your branch first makes the final merge into main a "clean" one.

### 1️⃣ Download the latest updates: Grab everything from the server.

To avoid conflicts and ensure your current branch (fix/bug_ticket_1235) is up-to-date:

```
# go back to main branch
git checkout main

# check for updates
git fetch origin main

# check the changes made
git status
```
### 2️⃣ Merge into your branch: Combine the new main code into your current fix branch.

If there are changes on the main branch then run following commands:

```bash
git pull origin main
git checkout fix/bug_ticket_1235
git merge origin/main
```

---

### 🚀 Pro-Tip: The "One-Liner"

If you don't want to keep switching back and forth to the main branch, you can do this while staying on your fix branch:

❌ Instead of doing this:

```
git checkout main
git pull origin main
git checkout fix/bug_ticket_1235
git merge origin/main
```
✅️ Simply stay on your fixing branch and run following commands:

```
git fetch origin main  # Download newest stuff from server
git merge origin/main  # Merge that data directly into your fix branch
```
### 💡 Why the "Pro" way wins:

* **You never have to leave your fix branch**, and your local main stays out of the way.
* **No Context Switching:** You don't have to checkout main, wait for your IDE to reload files, then checkout back.
* **Cleaner Local Main:** Your local main branch doesn't even need to be updated. You’re pulling from the "source of truth" (the server) directly into your feature.
* **Speed:** It’s fewer commands and less disk activity for your computer.

By using `git fetch origin main`, you download the latest code into a hidden folder (the remote-tracking branch `origin/main`)
without touching your own files. Then, `git merge origin/main` brings those specific updates into your work.

### 💡 Why this works?

In Git, `git pull` is essentially a combination of `git fetch` followed immediately by `git merge`. By breaking these apart, you gain more control:

* `git fetch origin main`: Specifically downloads the latest history from the `main` branch on the server (`origin`) and
stores it in your local remote-tracking branch, usually named `origin/main`.
* `git merge origin/main`: Integrates those specific downloaded changes into your current branch (e.g., `fix-branch`)
without ever needing to touch your local `main` branch.

⚠️ _One small catch: If you ever actually need to work on your local main branch later, it will still be "old" until you
eventually run `git pull` on it. But for daily development on a fix branch, the Pro way is much faster._

---

### 3️⃣ If used `git stash` bring your work back: Pop your changes out of storage and put them back on top.

```
git stash pop
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

## 🔹 Step 6 — 🚀 Push the branch

```bash
git push

# if it's a new branch run following command:
git push --set-upstream origin fix/bug_ticket_1235
# or a shortcut:
git push -u origin fix/bug_ticket_1235

```
---



## 🔹 Step 7.a. Before creating PR do `git merge main` (IMPORTANT)

To avoid conflicts and ensure your branch is up-to-date.

**Merge says:** "Take the new changes from main and tie them to my branch with a knot (a merge commit)."

A "**Merge-based**" strategy is more transparent and less risky for beginners then rebase—merging because it doesn't rewrite history.

```bash
# go back to main branch
git checkout main

# check for updates
git fetch origin main

# check the changes
git status
```

If there are changes run following commands:

```bash
git pull main
git checkout fix/bug_ticket_1235
git merge origin/main
```

---

## 🔹 7.b. Before creating PR (IMPORTANT)

To avoid conflicts and ensure your branch is up-to-date: (same file changed in both branches).

**Rebase says:** "Lift up my work, let the new main changes slide in underneath, and then put my work back on top."

It rewrites history: It technically deletes your old commits and creates brand new ones. If someone else is also working
on your branch, their Git will get very confused.

Rebase and resolve (or skip if safe):


```bash
git fetch origin
git rebase origin/main
# Result: Your commits just move to the very tip of the timeline.
# No extra "Merge" commit.
git push --force-with-lease
```

👉 Always rebase your branch on the latest main before creating a pull request.

🧠 Why force push is needed
After rebase: Git rewrites commit history

So normal push won’t work → you MUST use:

`git push --force-with-lease`

#### 🎯 Note: Rebase only when needed (before PR or when branch is outdated), not after every commit.


---

---

### 8. Create Pull Request (PR)

- Go to GitHub
- Click "Compare & pull request"
- Add description
- Submit PR

---

### 9. Merge PR

- Use "`Squash and merge`" (recommended)
- Ensures clean commit history

---

## 🔹 Step 10 — 🗑️ Cleanup (Delete branch)

### 1️⃣ 🌿 Delete remote branch (GitHub)
- Click "Delete branch"

or in CLI run this command:

```bash
git push origin --delete fix/bug_ticket_1235
```

### 2️⃣ 🌿 Delete local branch (Local Cleanup)

If you used "`Squash and Merge`" on GitHub, your local machine might think your branch isn't fully merged yet
(because the commit IDs changed during the squash).

```bash
# 1. Switch to another branch (usually main):
git checkout main
# 2. Pull last update:
git pull origin main
# 3. Delete the branch:
git branch -d fix/bug_ticket_1235
# or
git branch -D fix/bug_ticket_1235

```
📝 Note: If `git branch -d fix/bug_ticket_1235` gives you an error, use the capital `-D` to force delete it, since you know the work is safe on GitHub:

---


### 11. Optional: Clean stale branches

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

## 🧠 Troubleshooting - conflict
A conflict happens when the same file is changed in two branches and Git cannot decide which version to keep when combining them.

You can encounter a conflict like:

1. You had a branch e.g. `bug/ticket4375`
2. Meanwhile `main` got new changes. Someone (or you via another PR) updated main.
3. Both changed the same files. Both you and main modified for example: `README files`
4. Then you tried to combine them → conflict. So Git said: I don't know which version is correct"
5. What triggered the conflict: `Conflict = same file changed in two places + you try to combine them`
6. In my case, combining happened during: `git rebase origin/main`

- Conflict = same file changed in both branches
- Fix = rebase and resolve (or skip if safe)


### 🔧 How to fix it

`git rebase --skip`

👉 Meaning: "Ignore this problematic commit"

Git saw those changes already existed → skipped them → no conflict

### 🧠 Why it worked

`Your commits (line ending changes) were already in main`

So skipping = safe ✅

## 🚀 How to avoid this in the future
✅ Rule 1 — Keep your branch updated

Before finishing work or creating PR:

```
git fetch origin
git rebase origin/main
```

✅ Rule 2 — Don’t wait too long

If you work for a long time on a branch:

`Rebase occasionally (once per day is enough)`

✅ Rule 3 — Expect conflicts on shared files

👉 Change often → higher chance of conflict

✅ Rule 4 — Don’t panic

`Conflicts are normal in Git`

They do NOT mean:

* you did something wrong ❌
* your code is broken ❌

### ⚠️ One-line prevention rule
Always rebase your branch on the latest main before creating a pull request.



---


# 🔒 3. Protect main branch (GitHub)

## Steps:
1. Go to repository → Settings
2. Click **Branches**
3. Add rule for `main`

## 📌 Recommended settings:
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

## 🔍 Check history of commits.
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
## 7. 🍒 git cherry-pick

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

## 🔀 8. Switching Branches

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

## 9. 🔗 Upstream Branch (Tracking)

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

# ⚡ Git Shortcuts (set, edit, delete)

## 🗃️ Set shortcut:

```
git config --global alias.lg "log --oneline --graph --decorate --all -10"
```

📝 _Note: You don't need --no-pager inside the Git alias because Git aliases automatically handle the output correctly,
but you can add it if you strictly want to bypass the pager._

### 🔥 Now you only run shortcut:

```
git lg
```

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


## 🗑️ How to Delete an Alias
If you want to start over or remove it entirely:

```
git config --global --unset alias.lg
```


---

# 📚 Configuration file  .pre-commit-config.yaml

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

* The pipeline runs `pre-commit run --all-files`.
* If it fails, the **Merge Request (MR)** or **Pull Request (PR)** is blocked. You cannot merge broken or poorly formatted code.

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

## 🔍 Git Fetch vs. Git Pull
In Git, `git fetch` is a "safe" command that downloads the latest changes (commits, files, and branches) from a remote repository
(like GitHub) to your local machine without merging them into your actual work.

Think of `git fetch` as checking the mail and git pull as opening the mail and acting on it.

### 1. The "Safety First" Approach

- Scenario: You know your teammate pushed code, but you're worried it might break your current work.
- Command: `git fetch`
- Result: You can now see their new commits in your history (via git log), but your code files don't change.
You are safe to keep working.

### 2. The "Update Me Now" Approach

- Scenario: You just sat down to work and want your local files to match exactly what is on GitHub right now.
- Command: `git pull`
- Result: Git downloads the data and updates your files immediately. If there are conflicts, you'll have to fix them right now.

### 3. The "Comparison" Approach

- Scenario: You want to see exactly how many commits you are "behind" the rest of the team.
- Commands:
    ```
    git fetch (Updates your local records)
    git status
  ```
- Result: Git will tell you: "Your branch is behind 'origin/main' by 3 commits." No files were moved or changed in the process.


| Command | What it does | Impact on your code |
| :--- | :--- | :--- |
| **git fetch** | Downloads data from remote | **None.** Only updates remote tracking. |
| **git pull** | `git fetch` + `git merge` | **Updates your local files** immediately. |

---
## Git logs:
..........

```
git log --oneline --graph
```

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


# blablabla...
