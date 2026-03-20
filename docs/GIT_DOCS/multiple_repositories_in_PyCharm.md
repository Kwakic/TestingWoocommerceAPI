## To handle multiple repositories in PyCharm, you can use a combination of terminal commands for simultaneous pushing and built-in UI menus for individual pushes.

### 1. Push to Both Simultaneously
To push to both GitLab and GitHub with a single command, you can create a special "combined" remote. Open the Terminal at the bottom of PyCharm and run:

1. Create a new remote called both:

    `git remote add both <GitLab-URL>`

2. Add the GitHub URL to the same remote:

    `git remote set-url --add --push both <GitHub-URL>`

3. Add the GitLab URL again as a push URL (this ensures the first one isn't overwritten):

    `git remote set-url --add --push both <GitLab-URL>`

Now, whenever you want to push to both, run git push both in the terminal.

### 2. & 3. Push to GitLab or GitHub Only

You can do this directly through the PyCharm interface without using the terminal:

1. Open the Push Dialog: Press Ctrl + Shift + K (Windows/Linux) or Cmd + Shift + K (macOS).
2. Choose Your Target:
   - Look at the top of the dialog where it lists the remote and branch (e.g., origin: main).
   - Click on the remote name (origin or github).
   - A dropdown will appear. Select the specific remote you want to target (e.g., your GitLab remote for option 2, or your GitHub remote for option 3).
3. Confirm: Click Push.

### Summary of Remotes

* To push to GitLab only: Select your GitLab remote (usually origin) in the Push dialog.
* To push to GitHub only: Select your github remote in the Push dialog.
* To push to both: Use the terminal command git push both (after setting it up once).


## In PyCharm, you can verify your destination in three ways before you hit "Push."

### 1. Check the "Push Commits" Dialog (Visual Check)
When you press Ctrl + Shift + K (Windows/Linux) or Cmd + Shift + K (macOS), the Push dialog appears.

* The Label: Look at the blue text on the left, just above your list of commits. It will say something like `main -> origin: main or main -> github: main`.
* The Target: The part after the -> is your destination.
  - `origin` usually points to GitLab.
  - `github` (or whatever you named the second remote) points to GitHub.

### 2. Check the Status Bar (Quick Check)
Look at the bottom-right corner of your PyCharm window.

* It displays your current branch name (e.g., Git: main).
* If you click this, a popup appears showing Local Branches and Remote Branches.
* The branch that has a blue cloud icon or is listed as "tracked" will show you which remote it is currently linked to by default.

### 3. Use the Terminal (Technical Check)
If you want to be 100% sure of which URLs are linked to which names, open the Terminal tab at the bottom and type:

bash
`git remote -v`

Use code with caution.
This will print a list of your remotes and their URLs:

* `origin` -> (GitLab URL)
* `github` -> (GitHub URL)

### How to Switch "on the Fly"

If the Push dialog shows origin (GitLab) but you want to push to GitHub instead, click the name origin right in that dialog. 
It will turn into a dropdown or text field, allowing you to select your github remote before you confirm the push.

## To permanently change which remote your branch tracks (so it defaults to either GitHub or GitLab every time you open the Push dialog), you need to `update the Upstream Branch`.

### Method 1: Using the PyCharm UI (Easiest)

1. **Open the Branches Menu:** Click the Git branch name in the bottom-right corner of the status bar (e.g., `Git: main`).
2. **Select Your Local Branch:** Find your current branch under the "**Local Branches**" section.
3. **Set Upstream:**
   - Hover over the branch and click the **three vertical dots** (or right-click it).
   - Select **Rename...** (Only if you want to change the local name) OR look for **Set Upstream Branch**.
   - If "Set Upstream" isn't visible there, click Push (Ctrl + Shift + K).
   - In the Push dialog, click the remote name (e.g., origin) and change it to github.
   - Check the box that says "Push to..." or ensures it saves the tracking reference.

### Method 2: Using the Terminal (Most Reliable)
If you want to force the main branch to track GitHub by default from now on, run this command in the PyCharm terminal:

bash
`git branch --set-upstream-to=github/main main`

_(Replace github with your remote name and main with your branch name if they are different.)_

### How to verify it worked:
Next time you press `Ctrl + Shift + K`, the dialog should automatically suggest:
`main -> github: main` instead of `origin`.

### Quick Tips for your New Workflow:
- **Defaulting to GitLab:** Run git branch --set-upstream-to=origin/main main.
- **The "Both" Remote:** If you set up the both remote we discussed earlier, you can even set that as the default: `git branch --set-upstream-to=both/main main`.

To permanently change which remote your branch tracks, you need to update the **Upstream Branch**.

#### Method 1: Using the PyCharm UI

1. Open the Branches Menu: Click the Git branch name in the bottom-right corner of the status bar.
2. Select Your Local Branch: Find your current branch under the "Local Branches" section.
3. Set Upstream:
   - Hover over the branch and click the **three vertical dots** (or right-click it).
   - Select **Set Upstream Branch.**
   - If "Set Upstream" isn't visible there, click **Push**.
   - In the Push dialog, **click the remote name** and change it to the desired remote.
   - **Check the box** that says "**Push to...**" or ensures it saves the tracking reference.

#### Method 2: Using the Terminal
To force a branch to track a specific remote by default, run this command in the terminal:

bash
`git branch --set-upstream-to=<remote_name>/<branch_name> <branch_name>`

_(Replace <remote_name> with your remote name and <branch_name> with your branch name.)_

#### How to verify it worked:
Next time you press your push shortcut, the dialog should automatically suggest the new remote.

## TROUBLESHOOTING 

If you receive this error:

      `$ git push
      fatal: The current branch main has no upstream branch.
      To push the current branch and set the remote as upstream, use
      
      git push --set-upstream origin main
      
      To have this happen automatically for branches without a tracking
      upstream, see 'push.autoSetupRemote' in 'git help config'`

That error just means your local
main branch is "homeless"—it doesn't know which remote (GitLab or GitHub) should be its default partner.
Since you want to be able to choose or set a default, here is how to fix that:

### 1. To set GitLab as the default
Run this in your terminal:   

`git push -u origin main`

### 2. To set GitHub as the default
Run this in your terminal:

`git push -u github main`

_(Note: -u is shorthand for --set-upstream. Once you do this once, you can just type git push in the future and it will 
remember your choice.)_

### 3. To push to Both (if you set up the 'both' remote earlier)
Run this:
bash

`git push -u both main`

### How to check who is the "Default" partner now:
If you ever forget who your branch is talking to, type:
bash

`git branch -vv`

It will show something like main [github/main] or main [origin/main]. The name in the brackets is your permanent default.

#### Pro Tip: Make Git smarter

If you want Git to automatically set up this "partnership" every time you create a new branch in the future, run this:
bash

`git config --global push.autoSetupRemote true`

`This command
tells Git to automatically create and link remote branches the first time you push them, so you never have to see the 
"fatal: The current branch has no upstream branch" error again. `

**How it works:**

- The Problem: Normally, when you create a new local branch and try to run git push, Git stops you because it doesn't 
know where on the server to put it. You are forced to type git push --set-upstream origin your-branch-name.
- The Fix: With this setting enabled, you can just type git push. Git will automatically:
  - Create a branch with the same name on your remote (like GitHub or GitLab).
  - Set up "tracking," meaning your local branch is now officially "linked" to that remote version. 

**Breaking down the command:**

- `git config:` Accesses your Git settings.
- `--global:` Applies this change to every repository on your computer, not just the current one.
- `push.autoSetupRemote true:` Enables the specific feature that assumes `--set-upstream` on your behalf. 

**Why use it?**
It is a "set it and forget it" quality-of-life improvement introduced in Git 2.37.
It saves you from having to copy-paste that long "fatal" error message every time you start a new branch. 

## Switch between GitLab and GitHub
If you prefer using the PyCharm buttons:

1. Press Ctrl + Shift + K (or Git > Push).
2. Look at the top of the popup where it says origin. Click the word origin and a dropdown will appear.
3. Select GitHub from the list.
4. Click Push.


1. Check your current branch by running:: `git branch -vv`
2. List all the remote servers : `git remote -v`
3. Switching: Run this to tell Git that, from now on, main should point to your GitHub remote by default:
`git push -u GitHub main` or `git push -u origin main` for GitLab.
4. To make sure it has changed check your current branch again by running:: `git branch -vv`

- Using GitLab add (or manually in Pycharm: Menu/git/manage remotes):
   - `git remote set-url origin git@gitlab.com:kwakino/ecommerce.git`
   - `git push origin main`

- Using GitHub add (or manually in Pycharm: Menu/git/manage remotes):
   - `git remote set-url origin git@github.com:Kwakic/TestingWoocommerceAPI.git`
   - `git push GitHub main`
  
## To switch between branches in the CLI
### 1. The Modern Way (Recommended):
Starting with Git 2.23, a more intuitive command was added specifically for moving between branches:
`git switch main`

To go back to your bug branch: `git switch QA_bug_4567`

### 2. The Classic Way
The older, most common command used by most developers is: `git checkout main`


### 3. The "Quick Toggle" Pro-Tip
If you want to jump back to the previous branch you were just on (without typing the name), use a hyphen:
bash

`git switch -`
OR
`git checkout -`

---

### CREATE NEW BRANCH  
#### The flow is: 

`main → create branch → commit → push → Pull Request → merge → delete branch`

This gives you This gives you:
* safer changes
* code review (even if it's just you)
* clean history
* rollback capability

Here is the exact sequence you’ll use every time you start a new task:

1. Create & Switch: `git checkout -b QA_bug_4567` (This creates and moves you to the branch).
2. Work: Edit your code in PyCharm.
3. Stage: `git add .` (Prepares all changed files).
4. Commit: `git commit -m "fixed the bug in the login flow"` (Saves the snapshot locally).
5. Push & Link: `git push -u GitHub QA_bug_4567` (Uploads it and connects it to GitHub).
6. Create a Pull Request (PR): Since the branch is now on GitHub, you (or a teammate) go to the GitHub website to 
review the code. This is where you "propose" merging your bug fix into the main branch.
7. Merge: Once the code is approved and the tests pass, you click Merge on GitHub. This officially moves your 
**QA_bug_4567** code into the main branch.
8. The "Cleanup" (Delete): This is when you delete the branch. You don't need it anymore because the code is safely 
inside main.
   * On GitHub: There is usually a button that says **"Delete branch"** right after you merge.
   * On your computer (PyCharm):
       - Switch back to main: `git checkout main` or `git switch main`
       - Update your main: `git pull`
       - Delete the local bug branch: `git branch -d QA_bug_4567`

### Summary of "Best Practice"
You only delete the branch after the code has been successfully merged into the main codebase. Deleting it right after 
Step 5 would be like throwing away the ladder before you've finished climbing onto the roof!


**Note:** The -u (or --set-upstream) flag is important—it links your local branch to the remote one so that in the future,
you can just type git push or git pull without specifying the name again.

### To fully remove the branch from
PyCharm's memory so it stops showing up in your lists, you need to "prune" your local view. PyCharm keeps a local record 
of what was on GitHub until you tell it to refresh.

1. Prune the Remote References (The "Ghost" Branch)
Even though you deleted it on GitHub, PyCharm still thinks origin/QA_bug_4567 exists.
   * Go to the top menu: Git > Fetch.
   * Alternative (CLI): Run git fetch GitHub --prune.
   * This tells PyCharm: "Check GitHub again and remove any branches that are gone from the server."
   
2. Delete the Local Branch
PyCharm won't delete your local copy of the code automatically (to protect your work).
   * Open the Branches menu (bottom-right corner or top-left in the New UI).
   * Find QA_bug_4567 under the Local Branches section.
   * Hover over it, click the three dots (or right-click), and select Delete.
   * If a popup asks if you're sure because it's "not fully merged" (due to the Revert), click Delete Anyway.
   
3. Clear the "Recent" List
If you still see the name in the search bar or "Recent" list:
   * Open the Git tool window (Alt + 9).
   * Go to the Log tab.
   * On the left sidebar under Branches, right-click any branch that shouldn't be there and select Delete.