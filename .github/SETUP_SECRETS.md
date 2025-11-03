# GitHub Secrets Setup Guide

## Required Secrets for GitHub Actions

To enable automated data collection and deployment, you need to add the following secrets to your GitHub repository.

### 1. Navigate to Repository Settings

1. Go to your GitHub repository: **https://github.com/zpsy-hub/may-pasok-ba**
2. Click **Settings** (top right)
3. In left sidebar, click **Secrets and variables** → **Actions**

### 2. Add Required Secrets

Click **New repository secret** for each of these:

#### `SUPABASE_URL`
- **Value**: Your Supabase project URL
- **Format**: `https://xxxxxxxxxxxxx.supabase.co`
- **Where to find it**:
  1. Go to [Supabase Dashboard](https://app.supabase.com)
  2. Select your `suspension-predictions` project
  3. Click **Settings** (gear icon) → **API**
  4. Copy the **Project URL**

#### `SUPABASE_KEY`
- **Value**: Your Supabase service role key
- **Format**: `eyJhbGc...` (long JWT token)
- **Where to find it**:
  1. Same location as above (Settings → API)
  2. Copy the **`service_role` key** (NOT the anon key!)
  3. Click "Reveal" to see the full key
  
**⚠️ Important**: Use the `service_role` key, not the `anon` key. The service role key allows write access to the database.

### 3. Verify Secrets

After adding both secrets, your Actions secrets page should show:
- ✅ `SUPABASE_URL`
- ✅ `SUPABASE_KEY`

### 4. Test the Workflow

1. Go to **Actions** tab in your repository
2. Click **Deploy to GitHub Pages** workflow
3. Click **Run workflow** → **Run workflow**
4. Wait for the workflow to complete (~2-3 minutes)
5. Check the summary for prediction results

### Security Notes

🔒 **Never commit these values to your repository!**
- Secrets are encrypted and only accessible to GitHub Actions
- The service role key bypasses Row Level Security (RLS) for database writes
- The workflow uses environment variables to access secrets securely

### Troubleshooting

#### "Invalid API key" error
- Make sure you copied the **service_role** key, not the anon key
- Check for extra spaces when pasting the key
- Verify the key in Supabase dashboard is still active

#### "Connection refused" error
- Double-check the SUPABASE_URL format (must include `https://`)
- Ensure your Supabase project is not paused (free tier pauses after inactivity)
- Check Supabase status page: https://status.supabase.com

#### Workflow fails on first run
- This is normal! GitHub Actions needs to install dependencies
- The first run may take 3-5 minutes
- Subsequent runs will be faster (~1-2 minutes)

### Next Steps

After setting up secrets:
1. ✅ Secrets configured
2. ✅ Workflow will run automatically every hour
3. ✅ Manual runs available via Actions tab
4. ✅ Predictions will be deployed to GitHub Pages
5. ✅ Data logged to Supabase database

**Automation Status**: 🟢 Active (runs every hour at :00)

---

**Last Updated**: November 2, 2025  
**Workflow**: `.github/workflows/deploy.yml`
