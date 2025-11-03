# 🚀 GitHub Actions Deployment Checklist

Complete these steps to activate automated hourly predictions.

## ✅ Pre-Deployment Checklist

### 1. Database Setup
- [x] Created Supabase account
- [x] Deployed `database/schema.sql` to Supabase
- [x] Tested connection with `database/supabase_client.py`
- [ ] Copy Supabase URL (format: `https://xxxxx.supabase.co`)
- [ ] Copy Supabase service_role key (starts with `eyJhbG...`)

### 2. Local Testing
- [x] Tested weather collection: `python src/weather/weather_pipeline.py`
- [x] Tested PAGASA scraper: `python src/weather/pagasa_checker.py`
- [x] Tested full pipeline: `python scripts/collect_and_log.py`
- [x] Verified predictions: `web/predictions/latest.json` exists
- [x] Confirmed ML model loads successfully (no fallback warnings)

### 3. GitHub Repository
- [x] Code pushed to main branch
- [x] Repository is public (for GitHub Pages)
- [ ] GitHub Pages enabled (Settings → Pages)
- [ ] Actions enabled (Settings → Actions)
- [ ] Workflow permissions: Read and write (Settings → Actions → General)

## 🔐 Add GitHub Secrets

### Step-by-Step Guide

1. **Navigate to Secrets**
   ```
   Your repo → Settings → Secrets and variables → Actions
   ```

2. **Add SUPABASE_URL**
   - Click "New repository secret"
   - Name: `SUPABASE_URL`
   - Value: Your Supabase project URL
     ```
     https://xxxxxxxxxxxxx.supabase.co
     ```
   - Click "Add secret"

3. **Add SUPABASE_KEY**
   - Click "New repository secret"
   - Name: `SUPABASE_KEY`
   - Value: Your Supabase service_role key (long JWT token)
     ```
     eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
     ```
   - Click "Add secret"

4. **Verify Secrets**
   - You should see 2 secrets listed:
     - ✅ `SUPABASE_URL`
     - ✅ `SUPABASE_KEY`

## 🌐 Enable GitHub Pages

1. Go to **Settings** → **Pages**
2. Under "Build and deployment":
   - Source: **Deploy from a branch**
   - Branch: **gh-pages** (will be created by workflow)
   - Folder: **/ (root)**
3. Click **Save**
4. Note your site URL: `https://zpsy-hub.github.io/may-pasok-ba`

## ⚙️ Configure Actions Permissions

1. Go to **Settings** → **Actions** → **General**
2. Scroll to "Workflow permissions"
3. Select: **Read and write permissions**
4. Check: **Allow GitHub Actions to create and approve pull requests**
5. Click **Save**

## 🚀 First Deployment

### Option 1: Manual Trigger (Recommended)
1. Go to **Actions** tab
2. Click "Deploy to GitHub Pages" workflow (left sidebar)
3. Click "Run workflow" (right side)
4. Branch: **main**
5. Click green "Run workflow" button
6. Wait 2-3 minutes for completion

### Option 2: Automatic Trigger
1. Make a small commit (e.g., update README)
2. Push to main branch
3. Workflow will start automatically

### Option 3: Wait for Schedule
- Workflow runs automatically every hour
- Next run: At the top of the next hour (e.g., 3:00 PM)

## 🔍 Verify Deployment

### Check Workflow Status
1. Go to **Actions** tab
2. Find your workflow run
3. Look for green checkmark ✅
4. Click run to see detailed logs

### Expected Output
```
🎉 Deployment Summary
Run ID: 1234567890
Timestamp: 2025-11-02 14:00:00 UTC

📊 Prediction Summary
{
  "total_lgus": 17,
  "predicted_suspensions": 0,
  "avg_probability": 0.31
}

Predicted Suspensions: 0 / 17 LGUs
Average Risk: 31.0%

🌐 Live Site: https://zpsy-hub.github.io/may-pasok-ba
```

### Check Live Site
1. Visit: `https://zpsy-hub.github.io/may-pasok-ba`
2. Verify predictions are displayed
3. Check timestamp is recent

### Check Database
1. Go to Supabase dashboard
2. Click "Table Editor"
3. Check `daily_predictions` table has today's data
4. Check `collection_logs` table shows successful runs

### Check Predictions Files
1. Go to your repository
2. Navigate to `web/predictions/`
3. Verify `latest.json` was updated
4. Check timestamped file exists (e.g., `predictions_20251102_140000.json`)

## 🐛 Troubleshooting

### ❌ "Invalid API key" error
**Cause**: Wrong Supabase key  
**Fix**: 
1. Verify you used `service_role` key (not `anon` key)
2. Check for extra spaces when copying
3. Re-add secret if needed

### ❌ "Module not found" error
**Cause**: Missing dependencies  
**Fix**: 
1. Ensure `requirements.txt` includes all packages
2. Check workflow installs: `pip install -r requirements.txt`
3. Add missing package to requirements.txt

### ❌ "Permission denied" on push
**Cause**: Workflow can't write to repo  
**Fix**:
1. Settings → Actions → General
2. Enable "Read and write permissions"
3. Save and re-run workflow

### ❌ "Predictions file not found"
**Cause**: Pipeline failed  
**Fix**:
1. Check workflow logs for Python errors
2. Test locally: `python scripts/collect_and_log.py`
3. Verify model file exists: `model-training/data/processed/best_core_model.pkl`

### ❌ GitHub Pages shows 404
**Cause**: Pages not enabled or branch not created  
**Fix**:
1. Wait for first successful workflow run
2. Check `gh-pages` branch was created
3. Settings → Pages → Verify branch is `gh-pages`

## 📊 Monitoring

### Daily Checks (Optional)
- [ ] Visit Actions tab to verify runs are succeeding
- [ ] Check live site shows updated timestamps
- [ ] Spot-check Supabase for data quality

### Weekly Checks
- [ ] Review collection_logs for failure patterns
- [ ] Check prediction accuracy (once actual data is available)
- [ ] Monitor GitHub Actions usage (should be <1% of free tier)

### Monthly Checks
- [ ] Review model performance metrics
- [ ] Archive old prediction files if needed
- [ ] Update documentation if workflow changes

## 🎉 Success Indicators

You'll know deployment is successful when:

✅ Workflow shows green checkmark in Actions tab  
✅ Live site displays current predictions  
✅ Supabase tables have today's data  
✅ `web/predictions/latest.json` updated  
✅ Collection runs logged in database  
✅ No error emails from GitHub Actions  

## 📚 Next Steps

After successful deployment:

1. ✅ **Task 2 Complete**: GitHub Actions workflow active
2. ⏭️ **Task 4**: Build interactive dashboard with historical data
3. ⏭️ **Task 5**: Add comprehensive test suite
4. 🔄 **Monitor**: Check hourly runs for first 24 hours

## 🆘 Need Help?

- 📖 Read [.github/README.md](.github/README.md) for detailed docs
- 🔍 Check [existing issues](https://github.com/zpsy-hub/may-pasok-ba/issues)
- 💬 Create [new issue](https://github.com/zpsy-hub/may-pasok-ba/issues/new) with:
  - Workflow run ID
  - Error message
  - Screenshot of logs

---

**Last Updated**: November 2, 2025  
**Estimated Setup Time**: 10-15 minutes  
**Automation Status**: 🟡 Pending secrets configuration
