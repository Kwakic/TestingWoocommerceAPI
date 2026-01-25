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
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
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

Congratulations on mastering Git basics! 🎉