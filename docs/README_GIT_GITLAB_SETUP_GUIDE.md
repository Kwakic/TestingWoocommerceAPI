# Getting Started with Git and GitLab 🚀

This beginner-friendly guide will walk you through setting up Git in PyCharm, configuring SSH for GitLab, and making your first commit. Let’s get started!

---

## Overview 🛠️
The basic workflow (simplified):
1. **Your PC (PyCharm)**
   You write code here.
2. **GitLab Repo**
   Your code is stored securely.
3. **GitLab CI Pipeline**
   Automates your tests and deployment.
4. **Pytest Runs**
   Ensures your code works.

---

## Step 1: Initialize Git in PyCharm 🌟

1. Open your PyCharm project.
2. Navigate to:
   `VCS → Enable Version Control Integration`
3. Select:
   **Git**
   Your project is now a Git repository locally ✅

---

## Step 2: Set Up SSH for GitLab 🔐

### 2.1 Check for Existing SSH Keys
In PowerShell, run any of these commands to check for existing SSH keys:
```bash
Get-ChildItem $env:USERPROFILE\.ssh
ls ~/.ssh
ls $home\.ssh
```
Look for files like:
- `id_ed25519.pub` (Recommended modern format)
- `id_rsa.pub` (Older common format)

### 2.2 Display & Copy Your Public Key
**PowerShell**:
```bash
Get-Content $env:USERPROFILE\.ssh\id_rsa.pub
Get-Content $env:USERPROFILE\.ssh\id_rsa.pub | Set-Clipboard
```

**Git Bash**:
```bash
cat ~/.ssh/id_rsa.pub
cat ~/.ssh/id_rsa.pub | clip.exe
```
⚠️ **Reminder**: Never share the private key (`id_rsa`). Only share `id_rsa.pub`.

### 2.3 Add Your Public Key to GitLab
1. Go to GitLab → **Profile → Preferences → SSH Keys**.
2. Paste your public key, add a title (e.g., “Windows laptop”), and click **Add key**.

---

### 2.4 Fix Common SSH Agent Errors
If you encounter errors like `Cannot start service ssh-agent` in PowerShell:
1. Open PowerShell as Administrator.
2. Run:
```bash
Set-Service -Name ssh-agent -StartupType Automatic
Start-Service -Name ssh-agent
```
3. Add your private key to the agent:
```bash
ssh-add $env:USERPROFILE\.ssh\id_rsa
```

**Verify the key**:
```bash
ssh-add -l
```

---

### 2.5 Test SSH Connection to GitLab
Run:
```bash
ssh -T git@gitlab.com
```
Expected result:
```bash
Welcome to GitLab, @yourusername!
```

---

## Step 3: Turn Your Local Folder into a Git Repo 📂

### 3.1 Configure Your Git Identity
```bash
git config --shared user.name "Your Name"
git config --shared user.email "your.email@example.com"
```

### 3.2 Initialize the Local Repository
1. Go to your project’s root folder:
   ```bash
   cd C:\path\to\your\project
   ```
2. Initialize Git:
   ```bash
   git init
   ```

### 3.3 Add a Remote (GitLab)
Use the SSH URL, not HTTPS:
```bash
git remote add origin git@gitlab.com:yourusername/your-repo.git
```

Verify:
```bash
git remote -v
```

### 3.4 Rename the Branch (Optional)
If your branch is `master`, rename it to `main`:
```bash
git branch -M main
```

---

## Step 4: Add and Commit Your Code 📜

1. Optional: Add `.gitignore` and `.gitattributes` to your repo.
2. Add all files:
   ```bash
   git add .
   ```
3. Commit your changes:
   ```bash
   git commit -m "Initial commit"
   ```

---

## Step 5: Push Your Code to GitLab 🌍

1. Push your branch:
   ```bash
   git push -u origin main
   ```
2. If you encounter this error:
   ```bash
   ! [rejected]
   error: failed to push some refs to 'gitlab.com:...'
   ```
   Run:
   ```bash
   git pull origin main --allow-unrelated-histories
   git push -u origin main
   ```

---

## Troubleshooting 🔧

- **Permission denied (publickey):**
  - Confirm the correct public key is added to GitLab.
  - Check `ssh-add -l` to ensure your key is loaded.

- **Branch conflicts:**
  - Use `git pull origin main --allow-unrelated-histories`.

---

## Bonus: PyCharm Tips 💡

After pushing, PyCharm integrates Git seamlessly! Use the UI for:
- Commits
- Pushes/Pulls
- Visual diffs

---

## Your Mental Model Going Forward 🧠
The Git workflow:
1. Edit your code.
2. Check status:
   ```bash
   git status
   ```
3. Stage changes:
   ```bash
   git add .
   ```
4. Commit:
   ```bash
   git commit -m "Your message"
   ```
5. Push:
   ```bash
   git push
   ```

## ⚡ ROLLBACK IN GITLAB

To rollback a push in GitLab, you can either revert the changes (creating a new "undo" commit) or reset the history
(completely deleting the pushed commit). Reverting is the safest and recommended method for shared projects.


### Option 1: Revert (Recommended for shared branches)

This method keeps your history intact by adding a new commit that reverses your previous changes.

- #### Via GitLab Web Interface:
    1. Go to your project and select **Code > Commits**.
    2. Select the **title of the commit** you want to undo.
    3. In the upper-right corner, select **Options > Revert**.
    4. Choose your branch and select **Revert** to create a new merge request or commit immediately.
- #### Via Command Line:
    1. Find the commit hash using `git log.`
    2. Run: `git revert <commit_hash>`.
    3. Push the new revert commit: `git push origin <branch_name>`.

### Option 2: Reset (Best for personal/private branches)

This "rewinds" the branch to a previous state and permanently deletes the unwanted commit from the history.

- Warning: This can break the history for teammates who have already pulled your changes.

1. Reset locally:
   1. To keep your work but "un-push" it: `git reset --soft HEAD~1`.
   2. To delete the work entirely: `git reset --hard HEAD~1`.
2. Force push to GitLab: `git push origin <branch_name> --force.`
3.
   _1. Note: You may need to temporarily unprotect the branch in GitLab Settings to allow a force push._

### Option 3: Rollback a Deployment (CI/CD)
If your push triggered a deployment that broke your environment, you can roll back the deployed version without necessarily changing the code yet:

1. Go to Operate > Environments.
2. Select your environment (e.g., production).
3. Find a previously successful deployment and click the Rollback button next to it.

### SUMMARY NOTE:
**Option 1: Revert** is the standard "best practice" for any branch that other people might be using
(like `main`, `master`, or `develop`).

Here is why **Revert** is generally superior to **Reset** for rollbacks:

* **Preserves History:** It doesn't delete the "bad" commit; it just adds a new "undo" commit. This makes it clear to
your team what happened and why.
* **Safe for Collaboration:** If a teammate has already pulled your "bad" push, a revert won't break their local
repository. A reset (force push) can cause major merge conflicts for everyone else.
* **Undo the Undo:** If you realize later that the original push was actually correct, you can simply revert the revert
to bring the code back.
* **No Admin Rights Needed:** Many GitLab branches are "Protected," meaning you aren't allowed to force push (reset).
Reverting is just a standard commit, so it doesn't require changing any security settings.

### When should you not use Revert?
The only time you should choose Option 2 (Reset) instead is if you accidentally pushed sensitive data
(like a password or API key). Because a revert keeps the original commit in the history, the secret would still be
visible to anyone who looks at the commit logs.
