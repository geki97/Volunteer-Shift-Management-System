# 🔐 Repository Access Control - Admin Guide

## Overview

This repository has been configured with strict access controls to ensure only the repository owner (@geki97) can modify the code.

---

## Access Control Layers

### Layer 1: CODEOWNERS File
**File:** `.github/CODEOWNERS`

- Requires approval from `@geki97` for ALL changes
- Blocks direct commits to protected branches
- Forces pull request workflow

### Layer 2: Branch Protection Rules
**Applied to:** `master` and `main` branches

- ✅ Require pull request reviews before merging
- ✅ Dismiss stale PR approvals when new commits pushed
- ✅ Require code owner review
- ✅ Require status checks to pass before merge
- ✅ Include administrators in restrictions

### Layer 3: Repository Permissions
**GitHub Settings:** Repository Access

- Public visibility (read-only for anyone)
- Collaborators: None (only owner can push)
- Outside collaborators: None

### Layer 4: Webhook Restrictions
**Automated Protections**

- Only owner can create webhooks
- Audit logging enabled
- No unauthorized integrations allowed

---

## Setup Instructions

### Step 1: GitHub UI Configuration

1. Go to: **Settings → Branches**

2. Add branch protection rule for `master`:
   - ✅ Protect matching branches
   - ✅ Require a pull request before merging
   - ✅ Require approvals (1+)
   - ✅ Dismiss stale pull request approvals when new commits are pushed
   - ✅ Require review from Code Owners
   - ✅ Require status checks to pass before merging
   - ✅ Include administrators

3. Save

### Step 2: Enforce Repository Settings

1. Go to: **Settings → Access**

2. Configure Access Control:
   - Repository visibility: **Public**
   - Base role: None
   - Do not add any collaborators

3. Go to: **Settings → Manage access**
   - Ensure only your account shows as "Owner"

### Step 3: Protect Against Accidental Pushes

1. Go to: **Settings → Developer settings → Personal access tokens**

2. If you create any tokens:
   - Set expiration to 90 days
   - Limit to specific repositories only
   - Use fine-grained permissions

---

## How It Works

### For You (Repository Owner - @geki97)

**To make changes:**

```bash
# Create a feature branch
git checkout -b feature/your-feature

# Make changes
git add .
git commit -m "Description"

# Push to GitHub
git push origin feature/your-feature

# Create Pull Request on GitHub UI
# Review your own code (optional step)

# Merge to master
# (You can merge without review due to admin override, but it's good practice to review)
```

### For Anyone Else Who Forks the Repo

**They can:**
- ✅ Fork the repository
- ✅ Clone the repository
- ✅ Read the code
- ✅ Create their own modifications locally

**They CANNOT:**
- ❌ Push directly to your repository
- ❌ Create pull requests that bypass your approval
- ❌ Modify any code without your review
- ❌ Change repository settings
- ❌ Create releases or tags

---

## Security Features Enabled

| Feature | Status | Function |
|---------|--------|----------|
| Branch Protection | ✅ Enabled | Prevents force pushes |
| Code Owner Review | ✅ Required | Only you can approve |
| Status Checks | ✅ Required | Tests must pass |
| Admin Restrictions | ✅ Enforced | Applies to admins too |
| Stale PR Dismissal | ✅ Enabled | Old approvals invalidated |
| Require Branches Up to Date | ✅ Recommended | Before merge |

---

## Verification Checklist

After setting up, verify these are in place:

- [ ] CODEOWNERS file exists at `.github/CODEOWNERS`
- [ ] Branch protection rule on `master` branch
- [ ] "Require pull request reviews" is checked
- [ ] "Require Code Owner review" is checked
- [ ] "Include administrators" is checked
- [ ] No collaborators added to repository
- [ ] Repository is set to "Public"
- [ ] Only your account has "Owner" role

### Check Status
```bash
# See branch protection rules (via GitHub API)
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/geki97/Volunteer-Shift-Management-System/branches/master/protection
```

---

## Rules Enforcement

### ✅ What Will Be Blocked

- Direct pushes to `master` (even with SSH key)
- Force pushes: `git push --force`
- Rewriting history: `git reset --hard`
- Unsigned commits (if you enable that)
- Commits that don't pass CI/CD checks

### ✅ What Will Be Allowed

- Pull requests to `master` with your approval
- Your commits to feature branches
- Tags and releases (only by you)
- Documentation updates in PRs
- Collaborators via forking and PRs

---

## Automated Enforcement (Optional - Requires GitHub Actions)

Create `.github/workflows/enforce-access.yml`:

```yaml
name: Enforce Access Control

on: [pull_request]

jobs:
  verify-author:
    runs-on: ubuntu-latest
    steps:
      - name: Check PR Author
        if: github.event.pull_request.user.login != 'geki97'
        run: |
          echo "❌ Only @geki97 can modify this repository"
          exit 1
```

This adds an extra layer that auto-rejects PRs from anyone else.

---

## Maintenance

### Regular Security Audit

Every month, check:

1. **Repository Settings:**
   ```
   Settings → Access → Check for unexpected collaborators
   ```

2. **Recent Activity:**
   ```
   Insights → Network → View all commits
   ```

3. **Branch Protection Rules:**
   - Verify still active
   - Review dismissal policies

### Update Rules as Needed

If you want to add maintainers later:

```
# Edit .github/CODEOWNERS to add:
* @geki97 @trusted-user
```

---

## Access Revocation

### If You Need to Remove Your Own Access

This is rare, but if needed:

1. Go to **Settings → Access**
2. Remove own account (creates read-only state)
3. Contact GitHub Support to regain admin access

### Recover Access

Contact GitHub Support with proof of identity:
- **Support URL**: https://support.github.com/
- **Request Type**: "Repository Access Recovery"

---

## Testing the Restrictions

### Test 1: Verify Branch Protection
```bash
# Try to push to master directly (will fail)
git push origin local-branch:master
# Expected: "remote: error: protected branch"
```

### Test 2: Verify Code Owner Approval Required
1. Fork the repository on another account
2. Create a pull request
3. Verify it shows "Waiting for review from @geki97"

### Test 3: Verify Direct Push Blocked
```bash
# Even with force, should be blocked
git push origin --force master
# Expected: "remote: error: protected branch"
```

---

## Documentation

- **Repository:** https://github.com/geki97/Volunteer-Shift-Management-System
- **Branch:** master (protected)
- **Owner:** @geki97
- **Visibility:** Public (read-only for non-owners)

---

## Troubleshooting

### "Permission denied" when trying to merge

**Solution:** Set yourself as code owner in CODEOWNERS file (already done)

### PRs not showing CODEOWNERS requirement

**Solution:** 
1. .github/CODEOWNERS file must exist
2. May need to refresh GitHub page
3. Branch protection rule must be configured

### Want to allow specific collaborators?

**Edit .github/CODEOWNERS:**
```
* @geki97 @trusted-collaborator-username
```

Then those users can also approve PRs.

---

## GitHub API Reference

### Check branch protection
```bash
curl https://api.github.com/repos/geki97/Volunteer-Shift-Management-System/branches/master
```

### Update branch protection
```bash
curl -X PUT -H "Authorization: token TOKEN" \
  https://api.github.com/repos/geki97/Volunteer-Shift-Management-System/branches/master/protection \
  -d '{"required_status_checks":{"strict":true,"contexts":["continuous-integration/travis-ci"]},"enforce_admins":true,"required_pull_request_reviews":{"dismiss_stale_reviews":true,"require_code_owner_reviews":true}}'
```

---

## Summary

Your repository is now protected with multiple layers:

1. ✅ **CODEOWNERS** - Requires your approval
2. ✅ **Branch Protection** - Blocks direct pushes
3. ✅ **Repository Settings** - No collaborators
4. ✅ **Read-Only Access** - Public code, write-restricted

**Result:** Only you (@geki97) can modify the repository, while anyone can view and fork the code.

---

**Last Updated:** April 17, 2026  
**Protection Level:** Maximum (Single Owner)
