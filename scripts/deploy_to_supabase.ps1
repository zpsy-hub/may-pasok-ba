<#
PowerShell deploy script placeholder for Supabase.

This script expects the following environment variables to be set (GitHub Actions should pass them as secrets):
- $env:SUPABASE_PROJECT_REF
- $env:SUPABASE_ACCESS_TOKEN

Fill in the exact supabase CLI commands you want to run. Example (pseudo-steps):
  npm i -g supabase
  supabase login --token $env:SUPABASE_ACCESS_TOKEN
  supabase link --project-ref $env:SUPABASE_PROJECT_REF
  # then deploy hosting or edge functions
  supabase deploy --project-ref $env:SUPABASE_PROJECT_REF --site ./web

Note: Replace the above with the real supabase CLI commands from Supabase docs.
#>

param()

Write-Host "Deploy to Supabase placeholder script"

if (-not $env:SUPABASE_PROJECT_REF -or -not $env:SUPABASE_ACCESS_TOKEN) {
    Write-Host "SUPABASE_PROJECT_REF or SUPABASE_ACCESS_TOKEN not set. Aborting deploy." -ForegroundColor Yellow
    exit 1
}

Write-Host "Supabase project ref: $($env:SUPABASE_PROJECT_REF)"
Write-Host "(Not running real deploy commands in this placeholder.)"

# TODO: uncomment and replace with actual commands when ready
# npm install -g supabase
# supabase login --token $env:SUPABASE_ACCESS_TOKEN
# supabase link --project-ref $env:SUPABASE_PROJECT_REF
# supabase deploy --project-ref $env:SUPABASE_PROJECT_REF --site ./web

Write-Host "Deploy script completed (placeholder)."
