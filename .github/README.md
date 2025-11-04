# GitHub Actions Workflows

This directory contains automated workflows that power the **May Pasok Ba?** prediction system.

## Active Workflows

### 1. `deploy.yml` - Main Deployment Pipeline

**Schedule**: Every hour (at :00)  
**Trigger**: Manual, Push to main, Scheduled  
**Duration**: ~2-3 minutes  

#### What It Does:
1. ✅ **Checkout code** - Pulls latest codebase
2. ✅ **Setup environments** - Python 3.11 + Node.js 18
3. ✅ **Install dependencies** - All Python/Node packages
4. ✅ **Run collection pipeline** - `scripts/collect_and_log.py`
   - Fetches PAGASA typhoon/rainfall warnings
   - Collects Open-Meteo weather forecasts
   - Generates ML predictions for 17 LGUs
   - Logs all data to Supabase database
5. ✅ **Verify predictions** - Ensures JSON was generated
6. ✅ **Commit predictions** - Updates `docs/predictions/*.json`
7. ✅ **Deploy to GitHub Pages** - Publishes to live site
8. ✅ **Summary report** - Shows prediction stats

#### Environment Variables:
- `SUPABASE_URL` - Database connection URL (from secrets)
- `SUPABASE_KEY` - Service role key for writes (from secrets)
- `github.run_id` - Unique identifier for tracking

#### Output Files:
- `docs/predictions/latest.json` - Current predictions (17 LGUs)
- `docs/predictions/predictions_YYYYMMDD_HHMMSS.json` - Timestamped backup
- `weather_data/realtime_features_YYYYMMDD_HHMMSS.json` - Raw weather data

#### Database Tables Updated:
- `daily_predictions` - LGU-specific suspension predictions
- `weather_data` - Open-Meteo forecast data
- `pagasa_status` - PAGASA typhoon/rainfall warnings
- `collection_logs` - Pipeline run metadata

### 2. `ci.yml` - Continuous Integration (if exists)

**Schedule**: On pull requests  
**Purpose**: Run tests before merging

## Setup Instructions

### Prerequisites
1. ✅ Supabase database deployed (see `database/README.md`)
2. ✅ GitHub repository created
3. ✅ Trained ML model in `model-training/data/processed/`

### Step-by-Step Setup

#### 1. Add GitHub Secrets
See detailed guide: [SETUP_SECRETS.md](./SETUP_SECRETS.md)

Required secrets:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase service_role key

#### 2. Enable GitHub Pages
1. Go to **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: **gh-pages** / `root`
4. Click **Save**

#### 3. Enable GitHub Actions
1. Go to **Actions** tab
2. If prompted, click **I understand, enable Actions**
3. Workflows will appear after first push

#### 4. Test the Workflow
1. Go to **Actions** → **Deploy to GitHub Pages**
2. Click **Run workflow** (right side)
3. Select branch: `main`
4. Click **Run workflow**
5. Wait ~2-3 minutes for completion

#### 5. Verify Deployment
1. Check workflow completed successfully (green checkmark)
2. Visit your site: `https://zpsy-hub.github.io/may-pasok-ba`
3. Predictions should show current data
4. Check Supabase dashboard for logged data

## Workflow Features

### Automatic Hourly Updates
- Runs at **:00** every hour (e.g., 1:00, 2:00, 3:00 AM/PM)
- Collects latest PAGASA warnings
- Updates weather forecasts
- Regenerates predictions
- Deploys to live site

### Manual Triggers
- Click **Run workflow** in Actions tab
- Useful for testing or immediate updates
- Same process as scheduled runs

### Failure Handling
- If pipeline fails, workflow stops
- Error logged to GitHub Actions summary
- Previous predictions remain on site
- Alerts sent to repository watchers

### Commit History
- Each run creates a commit with predictions
- Format: `Update predictions - 2025-11-02 14:00 UTC [Run #123456]`
- Easy to track changes over time
- Can revert if needed

## Monitoring

### View Run History
1. Go to **Actions** tab
2. Click **Deploy to GitHub Pages**
3. See list of all runs (success/failure)
4. Click any run to see details

### Check Logs
Each workflow step shows detailed logs:
- Installation progress
- Collection pipeline output
- Prediction summary
- Deployment status

### Deployment Summary
After each run, check the **Summary** tab:
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

## Troubleshooting

### "Invalid API key" error
**Cause**: Incorrect or missing Supabase secrets  
**Fix**: 
1. Verify secrets in Settings → Secrets
2. Ensure using `service_role` key, not `anon`
3. Re-add secrets if needed

### "Module not found" error
**Cause**: Missing Python dependencies  
**Fix**: 
1. Check `requirements.txt` is up to date
2. Ensure all packages are listed
3. Re-run workflow (dependency cache may be stale)

### "Predictions file not found" error
**Cause**: Pipeline failed before generating JSON  
**Fix**:
1. Check logs for Python errors
2. Test locally: `python scripts/collect_and_log.py`
3. Verify model file exists in `model-training/data/processed/`

### "Push rejected" error
**Cause**: Branch protection or permission issues  
**Fix**:
1. Check **Settings** → **Actions** → **Workflow permissions**
2. Enable "Read and write permissions"
3. Save and re-run workflow

### Workflow doesn't run on schedule
**Cause**: Repository inactive or Actions disabled  
**Fix**:
1. Make a small commit to wake up repository
2. Check Actions are enabled in Settings
3. Verify cron syntax is correct

## Performance

### Typical Run Times
- **Setup** (checkout, install): 30-60 seconds
- **Data collection**: 10-15 seconds
- **Prediction generation**: 5-10 seconds
- **Deployment**: 20-30 seconds
- **Total**: ~2-3 minutes

### Resource Usage
- **Compute**: Free tier (2,000 minutes/month)
- **Storage**: Minimal (<1MB per run)
- **Bandwidth**: ~100KB per deployment
- **Cost**: **$0** (fully within free tier)

## Best Practices

### Secrets Management
- ✅ Store all credentials in GitHub Secrets
- ✅ Never commit `.env` files
- ✅ Rotate keys periodically (every 6 months)
- ✅ Use `service_role` key for Actions, `anon` key for web

### Workflow Efficiency
- ✅ Cache dependencies when possible
- ✅ Use `continue-on-error` only for non-critical steps
- ✅ Keep workflows under 5 minutes
- ✅ Log important metrics in summary

### Error Handling
- ✅ Validate inputs before processing
- ✅ Use try/catch in Python scripts
- ✅ Log errors to database (collection_logs table)
- ✅ Send notifications for critical failures

### Monitoring
- ✅ Check Actions tab weekly for failures
- ✅ Review Supabase logs for data quality
- ✅ Monitor GitHub Pages uptime
- ✅ Validate predictions make sense

## Future Enhancements

### Potential Improvements
1. **Slack/Email Notifications**: Alert on high suspension probability
2. **Multi-environment**: Separate staging/production workflows
3. **Automated Testing**: Run pytest before deployment
4. **Performance Metrics**: Track execution time trends
5. **Rollback Automation**: Auto-revert on deployment failures

### Advanced Features
1. **A/B Testing**: Deploy multiple model versions
2. **Blue-Green Deployment**: Zero-downtime updates
3. **Canary Releases**: Gradual rollout of changes
4. **Load Testing**: Stress test before major releases

## Related Documentation

- [Database Setup](../database/README.md) - Supabase configuration
- [Model Integration](../ML_MODEL_INTEGRATION.md) - ML model details
- [Pipeline Script](../scripts/collect_and_log.py) - Collection logic
- [Secrets Setup](./SETUP_SECRETS.md) - GitHub secrets guide

## Support

**Issues?** Open a GitHub issue with:
- Workflow run ID
- Error message
- Screenshot of logs
- Steps to reproduce

**Questions?** Check existing issues or create a discussion.

---

**Automation Status**: 🟢 Active  
**Last Updated**: November 2, 2025  
**Next Scheduled Run**: Check Actions tab for countdown

