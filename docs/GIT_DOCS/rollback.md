## ROLLBACK IN GITLAB

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