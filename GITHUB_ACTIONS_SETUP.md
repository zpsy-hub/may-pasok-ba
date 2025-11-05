# GitHub Actions Setup Guide

## ✅ Current Status

Your GitHub Actions workflow is **already configured** at:
- `.github/workflows/collect-predictions-docs.yml`

This workflow:
- ✅ Runs **hourly** (every hour at minute 0)
- ✅ Runs on **every push** to main branch
- ✅ Can be **manually triggered** via GitHub UI
- ✅ Collects weather data + PAGASA status
- ✅ Generates ML predictions
- ✅ Commits to repository
- ✅ Deploys to GitHub Pages

---

## 🔧 Setup Steps (One-Time Configuration)

### Step 1: Enable GitHub Actions

1. Go to your repository: https://github.com/zpsy-hub/may-pasok-ba
2. Click **Settings** tab
3. In left sidebar, click **Actions** → **General**
4. Under "Actions permissions", select:
   - ✅ **Allow all actions and reusable workflows**
5. Under "Workflow permissions", select:
   - ✅ **Read and write permissions**
   - ✅ **Allow GitHub Actions to create and approve pull requests**
6. Click **Save**

### Step 2: Add Supabase Secrets

1. In your repository, click **Settings** tab
2. In left sidebar, click **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these two secrets:

**Secret 1: SUPABASE_URL**
- Name: `SUPABASE_URL`
- Value: Your Supabase project URL (e.g., `https://abcdefghijk.supabase.co`)
- Click **Add secret**

**Secret 2: SUPABASE_KEY**
- Name: `SUPABASE_KEY`
- Value: Your Supabase **service_role** key (not anon key!)
- Click **Add secret**

**Where to find these:**
1. Go to https://supabase.com/dashboard
2. Select your project
3. Click **Settings** (gear icon) → **API**
4. Copy:
   - **URL** from "Project URL" section
   - **service_role** key from "Project API keys" section (click "Reveal" button)

### Step 3: Enable GitHub Pages

1. In your repository, click **Settings** tab
2. In left sidebar, click **Pages**
3. Under "Build and deployment":
   - **Source**: Deploy from a branch
   - **Branch**: `gh-pages` / `(root)`
   - Click **Save**
4. GitHub will show your site URL (e.g., `https://zpsy-hub.github.io/may-pasok-ba/`)

### Step 4: Verify Workflow is Enabled

1. Go to **Actions** tab in your repository
2. You should see "Deploy to GitHub Pages (docs)" workflow
3. If disabled, click **Enable workflow**

---

## 🚀 Running the Workflow

### Option 1: Automatic (Hourly)
- Workflow runs automatically every hour
- No action needed!

### Option 2: Manual Trigger
1. Go to **Actions** tab
2. Click **Deploy to GitHub Pages (docs)**
3. Click **Run workflow** dropdown
4. Click **Run workflow** button
5. Wait 2-3 minutes for completion

### Option 3: Push to Main
- Workflow runs automatically on every push to `main` branch
- Just commit and push your code!

---

## 📊 Monitoring Workflow Runs

### View Run History
1. Go to **Actions** tab
2. Click on any workflow run to see details
3. Check each step for success/failure

### View Logs
1. Click on a workflow run
2. Click on job name (e.g., "deploy")
3. Click on any step to see detailed logs

### Check Output
- **Predictions**: `docs/predictions/latest.json` in your repository
- **Website**: Your GitHub Pages URL (e.g., `https://zpsy-hub.github.io/may-pasok-ba/`)

---

## 🔍 Verifying Setup is Complete

Run this checklist:

- [ ] **GitHub Actions enabled** (Settings → Actions → General)
- [ ] **Workflow permissions set** (Read and write permissions)
- [ ] **SUPABASE_URL secret added** (Settings → Secrets)
- [ ] **SUPABASE_KEY secret added** (Settings → Secrets)
- [ ] **GitHub Pages enabled** (Settings → Pages)
- [ ] **gh-pages branch exists** (will be created on first run)
- [ ] **Workflow runs successfully** (Actions tab shows green checkmark)
- [ ] **Predictions file created** (docs/predictions/latest.json exists)
- [ ] **Website loads** (GitHub Pages URL accessible)

---

## 📦 Requirements.txt Status

Your `requirements.txt` is **already up-to-date** with all necessary packages:

✅ **Database**: `supabase`, `psycopg2-binary`
✅ **ML/Data**: `numpy`, `pandas`, `scikit-learn`, `imbalanced-learn`
✅ **Weather**: `openmeteo-requests`, `requests-cache`
✅ **Utilities**: `python-dotenv`, `requests`

**Missing package (needs to be added):**
- ❌ `imbalanced-learn` (for EasyEnsemble model)

Let me update your requirements.txt now...

---

## 🆘 Troubleshooting

### Problem: Workflow fails with "Permission denied"
**Solution**: Check workflow permissions in Settings → Actions → General

### Problem: Workflow fails with "Supabase authentication error"
**Solution**: 
1. Verify secrets are set correctly
2. Make sure you're using **service_role** key, not anon key
3. Check key hasn't expired

### Problem: Predictions file not generated
**Solution**: 
1. Check workflow logs in Actions tab
2. Verify `scripts/collect_and_log.py` runs locally first
3. Check for errors in "Run prediction collection script" step

### Problem: GitHub Pages shows 404
**Solution**:
1. Wait 2-3 minutes after first deployment
2. Check Settings → Pages shows "Your site is live"
3. Verify `docs/index.html` exists in repository
4. Check `gh-pages` branch was created

### Problem: Workflow runs but predictions outdated
**Solution**:
1. Check workflow schedule (hourly at minute 0)
2. Verify SUPABASE_KEY has write permissions
3. Check database connection in workflow logs

---

## 🎯 Next Steps After Setup

1. **Test workflow manually** (Actions → Run workflow)
2. **Check predictions generated** (docs/predictions/latest.json)
3. **Visit your website** (GitHub Pages URL)
4. **Monitor first 24 hours** for any errors
5. **Set up email notifications** (Settings → Notifications)

---

## 📧 Email Notifications (Optional)

To get notified when workflow fails:

1. Go to your GitHub profile → **Settings**
2. Click **Notifications** in left sidebar
3. Under "Actions":
   - ✅ Enable "Send notifications for failed workflows only"
   - ✅ Choose notification method (email, web, mobile)
4. Click **Save**

---

## 🔄 Workflow Execution Flow

```
Trigger (Hourly/Push/Manual)
        ↓
Checkout code
        ↓
Setup Python 3.11 + Node.js 18
        ↓
Install dependencies (pip + npm)
        ↓
Run collect_and_log.py
        ├→ Fetch weather (Open-Meteo API)
        ├→ Scrape PAGASA bulletins
        ├→ Generate ML predictions
        ├→ Save to database (Supabase)
        └→ Save to JSON (docs/predictions/latest.json)
        ↓
Commit & push JSON files
        ↓
Deploy to GitHub Pages (gh-pages branch)
        ↓
✅ Website updated!
```

**Total Duration**: ~2-3 minutes per run

---

## 📝 Quick Reference

| Action | Location | Notes |
|--------|----------|-------|
| **View workflows** | Actions tab | See all runs |
| **Run manually** | Actions → Deploy → Run workflow | Trigger on-demand |
| **Check secrets** | Settings → Secrets | Verify SUPABASE credentials |
| **View website** | Settings → Pages | Get GitHub Pages URL |
| **Edit workflow** | `.github/workflows/collect-predictions-docs.yml` | Modify schedule/steps |
| **View predictions** | `docs/predictions/latest.json` | Latest ML output |
| **Check logs** | Actions → [Run] → [Job] → [Step] | Detailed execution logs |

---

## ✨ Success Indicators

Your setup is working correctly when:

1. ✅ Actions tab shows green checkmarks
2. ✅ `docs/predictions/latest.json` updates hourly
3. ✅ GitHub Pages site loads with predictions
4. ✅ Database has new records (check Supabase dashboard)
5. ✅ No email notifications about failures

---

**Need help?** Check workflow logs in Actions tab or ask for assistance!
