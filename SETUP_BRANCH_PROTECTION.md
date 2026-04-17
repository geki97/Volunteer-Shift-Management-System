# ⚡ Quick Setup - Repository Access Control (5 Minutes)

## What We've Set Up

✅ **CODEOWNERS file** - Already in repository  
✅ **GitHub Actions workflow** - Automated verification  
✅ **Documentation** - REPOSITORY_ACCESS_CONTROL.md  

Now you need to enable branch protection on GitHub's website.

---

## Step-by-Step Setup (On GitHub.com)

### Step 1: Go to Repository Settings
1. Open: https://github.com/geki97/Volunteer-Shift-Management-System
2. Click: **Settings** (top menu)
3. Click: **Branches** (left sidebar)

### Step 2: Add Branch Protection Rule

#### Click "Add rule"

**Branch name pattern:** `master`

#### Check These Boxes:

☑️ **Protect matching branches**

☑️ **Require a pull request before merging**
- Set "Number of required reviewers": `1`

☑️ **Dismiss stale pull request approvals when new commits are pushed**

☑️ **Require review from Code Owners**

☑️ **Require status checks to pass before merging**
- If no checks yet, skip this (only if tests configured)

☑️ **Require branches to be up to date before merging**
- Optional but recommended

☑️ **Include administrators**
- This forces even you to use pull requests (best practice)

☑️ **Allow force pushes** - LEAVE UNCHECKED (security!)

☑️ **Allow deletions** - LEAVE UNCHECKED (security!)

#### Click: **Save changes**

---

### Step 3: Verify Repository Access Settings

1. Go: **Settings → Access**
2. Check:
   - Repository visibility: **Public** ✓
   - Base role: **None** (no default access)
   - Collaborators: **Zero** (only you)

### Step 4: Test It Works

#### Test from Another GitHub Account (or ask a friend):
1. Go to the repository
2. Click: **Fork**
3. Create a test file
4. Submit a Pull Request
5. GitHub should show: **"Review required - waiting for @geki97"**

If you see this, your setup is working! ✅

---

## What the Rules Do

| Scenario | Result |
|----------|--------|
| Anyone tries direct push | ❌ BLOCKED |
| Anyone creates PR | ⏳ Needs your approval |
| You merge your own PR | ✅ ALLOWED |
| Force push attempt | ❌ BLOCKED |
| Delete main branch | ❌ BLOCKED |

---

## Files We Created

```
.github/
├── CODEOWNERS                  ← Specifies you as code owner
└── workflows/
    └── access-control.yml      ← Automated verification checks
```

---

## Verification Checklist

After setting up branch protection, verify:

```
GitHub Settings → Branches → master rule
├── ☑ Protect matching branches
├── ☑ Require pull request reviews (1 reviewer)
├── ☑ Require Code Owner Review
├── ☑ Dismiss stale approvals
├── ☑ Include administrators
└── ☑ Require branches up to date
```

---

## Result

### Before Setup
- Anyone with repo access could push directly
- No approval process
- Risky for production code

### After Setup
- ✅ Only you can merge to master
- ✅ All changes require pull request
- ✅ Code owners must approve
- ✅ Automated checks run on all PRs
- ✅ Admin restrictions apply to everyone
- ✅ Force pushes blocked

---

## Important Notes

### ✅ You Can Still Push To Feature Branches

```bash
# Still works - feature branches not protected
git push origin feature/my-feature
```

### ✅ You Can Still Merge PRs

Your pull requests will show as approved automatically because you're the code owner.

### ✅ Automated Workflows Run

All PR checks will verify:
- Only @geki97 can modify
- No secrets in code
- No dangerous patterns

---

## Troubleshooting

### "I can't merge my own PR"

If using administrator override isn't enabled:
1. **Settings → Branches → master rule**
2. ☑ **Include administrators**
3. Save

### "CODEOWNERS isn't showing requirement"

1. Push the `.github/CODEOWNERS` file to GitHub
2. Close and reopen the PR
3. Requirement should appear

### "Branch protection rule not working"

1. Go to **Settings → Branches**
2. Verify rule is there and active
3. Try creating a new PR
4. Refresh the page

---

## GitHub API Verification

If you want to verify via command line:

```bash
# Install GitHub CLI
# https://cli.github.com/

# Verify branch protection
gh api repos/geki97/Volunteer-Shift-Management-System/branches/master/protection

# Should show your protection rules
```

---

## Next Steps

1. ✅ Make sure `.github/CODEOWNERS` is pushed to GitHub
2. ✅ Go to GitHub and set up branch protection rule on `master`
3. ✅ Test with a pull request from another account
4. ✅ Verify "Review required from @geki97" appears

---

## Security Best Practices

✅ **Enabled:**
- Branch protection on master
- Code owner review required
- Admin restrictions
- Stale PR dismissal
- Status checks required

❌ **Disabled (for security):**
- Force pushes
- Branch deletion
- Admin bypass
- Auto-merge

---

## Support

**Documentation:** `REPOSITORY_ACCESS_CONTROL.md`  
**Workflow:** `.github/workflows/access-control.yml`  
**Owner Config:** `.github/CODEOWNERS`

---

## Time to Complete

| Step | Time |
|------|------|
| Access GitHub Settings | 30 sec |
| Create branch protection | 2 min |
| Verify settings | 1 min |
| Test with PR | 1 min |
| **Total** | **~5 minutes** |

---

**You're Done!** Your repository is now protected. 🔐

Only @geki97 can modify the code while keeping it publicly accessible for viewers.
