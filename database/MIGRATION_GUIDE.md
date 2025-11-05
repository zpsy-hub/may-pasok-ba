# Database Migration Guide: Add Foreign Key Relationships

## 🎯 Goal
Add foreign key relationships between `daily_predictions`, `weather_data`, and `pagasa_status` tables **without losing any existing data**.

## ✅ Safety Guarantees

This migration is **100% safe**:
- ✅ **Zero data loss** - All foreign keys are nullable (optional)
- ✅ **Backward compatible** - Existing code continues to work unchanged
- ✅ **Rollback available** - Can undo completely if needed
- ✅ **ON DELETE SET NULL** - Predictions preserved even if weather/PAGASA deleted
- ✅ **No breaking changes** - UPSERT operations still work

## 📋 Pre-Migration Checklist

- [ ] **Backup database** in Supabase Dashboard → Settings → Database → Backup
- [ ] **Test in development** first (if you have a staging environment)
- [ ] **Verify current data count**:
  ```sql
  SELECT 'predictions' AS table_name, COUNT(*) FROM daily_predictions
  UNION ALL
  SELECT 'weather', COUNT(*) FROM weather_data
  UNION ALL
  SELECT 'pagasa', COUNT(*) FROM pagasa_status;
  ```
- [ ] **Note the counts** - verify same counts after migration

## 🚀 Migration Steps

### Step 1: Run Migration Script
1. Open Supabase Dashboard
2. Go to SQL Editor
3. Copy contents of `database/migration_add_relationships.sql`
4. Run the script
5. ✅ You should see: "Success. No rows returned"

### Step 2: Link Existing Records
Run these functions to populate foreign keys for existing predictions:

```sql
-- Link predictions to weather data
SELECT * FROM link_predictions_to_weather();

-- Expected output:
-- predictions_updated | predictions_with_weather | predictions_without_weather
-- 150                 | 150                      | 0

-- Link predictions to PAGASA status  
SELECT * FROM link_predictions_to_pagasa();

-- Expected output:
-- predictions_updated | predictions_with_pagasa | predictions_without_pagasa
-- 150                 | 140                     | 10
```

**Note**: Some predictions may not have matching PAGASA records (that's OK - they'll have NULL foreign keys).

### Step 3: Verify Migration
```sql
-- Check foreign key columns exist
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'daily_predictions'
  AND column_name IN ('weather_data_id', 'pagasa_status_id');

-- Check linking percentages
SELECT 
    'With weather link' AS category,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM daily_predictions), 2) AS pct
FROM daily_predictions
WHERE weather_data_id IS NOT NULL
UNION ALL
SELECT 
    'With PAGASA link',
    COUNT(*),
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM daily_predictions), 2)
FROM daily_predictions
WHERE pagasa_status_id IS NOT NULL;

-- Test new view
SELECT * FROM prediction_with_context LIMIT 5;
```

### Step 4: Verify Data Integrity
```sql
-- Verify no data was lost (counts should match pre-migration)
SELECT 'predictions' AS table_name, COUNT(*) FROM daily_predictions
UNION ALL
SELECT 'weather', COUNT(*) FROM weather_data
UNION ALL
SELECT 'pagasa', COUNT(*) FROM pagasa_status;
```

## 🔄 Update Application Code (Optional)

The migration is **backward compatible** - existing code works unchanged. But you can optionally update `supabase_client.py` to explicitly set foreign keys on insert:

### Option A: Automatic Linking (Recommended)
Let the database functions handle linking. Just insert predictions as usual:

```python
# Existing code - no changes needed!
logger.log_predictions(predictions, model_version='v1.0.0', threshold=0.5)
```

Then periodically run linking functions (e.g., daily cron job):
```sql
SELECT * FROM link_predictions_to_weather();
SELECT * FROM link_predictions_to_pagasa();
```

### Option B: Explicit Linking (Advanced)
Modify `supabase_client.py` to set foreign keys on insert:

```python
def log_predictions(
    self, 
    predictions: List[Dict[str, Any]],
    model_version: str,
    threshold: float
) -> Dict[str, Any]:
    records = []
    for pred in predictions:
        record = {
            'prediction_date': str(pred['prediction_date']),
            'lgu': pred['lgu'],
            'suspension_probability': float(pred['suspension_probability']),
            'predicted_suspended': bool(pred['predicted_suspended']),
            'model_version': model_version,
            'threshold_used': float(threshold),
            'github_run_id': self.github_run_id
        }
        
        # NEW: Optionally link to weather data
        if 'weather_data_id' in pred:
            record['weather_data_id'] = pred['weather_data_id']
        else:
            # Auto-lookup weather ID
            weather_result = self.client.table('weather_data')\
                .select('id')\
                .eq('weather_date', record['prediction_date'])\
                .eq('lgu', record['lgu'])\
                .eq('data_type', 'forecast')\
                .order('collected_at', desc=True)\
                .limit(1)\
                .execute()
            if weather_result.data:
                record['weather_data_id'] = weather_result.data[0]['id']
        
        # NEW: Optionally link to PAGASA status
        if 'pagasa_status_id' in pred:
            record['pagasa_status_id'] = pred['pagasa_status_id']
        else:
            # Auto-lookup PAGASA ID
            pagasa_result = self.client.table('pagasa_status')\
                .select('id')\
                .eq('status_date', record['prediction_date'])\
                .order('collected_at', desc=True)\
                .limit(1)\
                .execute()
            if pagasa_result.data:
                record['pagasa_status_id'] = pagasa_result.data[0]['id']
        
        records.append(record)
    
    response = self.client.table('daily_predictions').upsert(
        records,
        on_conflict='prediction_date,lgu'
    ).execute()
    
    return response.data
```

**Recommendation**: Start with **Option A** (automatic linking). It's simpler and works with existing code.

## 📊 Benefits After Migration

### 1. **Easier Queries with Joins**
```sql
-- Before: Manual join on dates
SELECT p.*, w.precipitation_sum
FROM daily_predictions p
LEFT JOIN weather_data w 
  ON p.prediction_date = w.weather_date 
  AND p.lgu = w.lgu
  AND w.data_type = 'forecast';

-- After: Direct foreign key join (faster, cleaner)
SELECT p.*, w.precipitation_sum
FROM daily_predictions p
LEFT JOIN weather_data w ON p.weather_data_id = w.id;
```

### 2. **Use the New View**
```sql
-- Get predictions with all context in one query
SELECT 
    prediction_date,
    lgu,
    suspension_probability,
    precipitation_sum,
    temperature_2m_max,
    wind_speed_10m_max,
    has_active_typhoon,
    typhoon_name,
    tcws_level
FROM prediction_with_context
WHERE prediction_date = '2025-11-06';
```

### 3. **Data Integrity Protection**
- Can't accidentally orphan predictions (foreign keys ensure references exist or are NULL)
- Database enforces relationships automatically
- Easier to debug data issues

## 🔙 Rollback (If Needed)

If something goes wrong, run this rollback script:

```sql
-- Remove foreign key constraints
ALTER TABLE daily_predictions DROP CONSTRAINT IF EXISTS fk_weather_data;
ALTER TABLE daily_predictions DROP CONSTRAINT IF EXISTS fk_pagasa_status;

-- Drop indexes
DROP INDEX IF EXISTS idx_predictions_weather_id;
DROP INDEX IF EXISTS idx_predictions_pagasa_id;

-- Drop helper functions
DROP FUNCTION IF EXISTS link_predictions_to_weather();
DROP FUNCTION IF EXISTS link_predictions_to_pagasa();

-- Drop view
DROP VIEW IF EXISTS prediction_with_context;

-- Optional: Remove columns (WARNING: Deletes link data)
-- Only run if you want to completely undo
-- ALTER TABLE daily_predictions DROP COLUMN IF EXISTS weather_data_id;
-- ALTER TABLE daily_predictions DROP COLUMN IF EXISTS pagasa_status_id;
```

**Note**: Rollback preserves all prediction, weather, and PAGASA data. Only the linking information is removed.

## ❓ FAQ

### Q: Will this break my GitHub Actions workflow?
**A:** No! The migration is backward compatible. Your existing `collect_and_log.py` script will continue to work unchanged. The foreign key columns are nullable, so they can be omitted on insert.

### Q: What if I have predictions without matching weather data?
**A:** That's fine! The foreign key will be NULL. Predictions are still valid and queryable. The linking functions skip records that don't have matches.

### Q: Do I need to update all my code?
**A:** No. Existing code works as-is. You can optionally update code to take advantage of foreign keys later.

### Q: Will this slow down inserts?
**A:** Minimal impact. Foreign key checks add ~1-2ms per insert. The ON DELETE SET NULL is safe and doesn't cascade deletes.

### Q: Can I run this on production?
**A:** Yes, but:
1. Backup first
2. Test in development if possible
3. Run during low-traffic period
4. Monitor for 24 hours after migration

## 📝 Thesis Documentation Update

After migration, update your thesis ER diagram to show:

```
┌─────────────────────────┐
│   daily_predictions     │
├─────────────────────────┤
│ id (PK)                 │
│ prediction_date         │
│ lgu                     │
│ weather_data_id (FK)────┼──→ weather_data.id
│ pagasa_status_id (FK)───┼──→ pagasa_status.id
│ suspension_probability  │
│ predicted_suspended     │
│ ...                     │
└─────────────────────────┘
```

Add to Section 4.6.1 (Database Schema):
> **Foreign Key Relationships:** The system uses optional foreign keys to link predictions with their corresponding weather forecasts and PAGASA status records. These relationships are nullable to maintain backward compatibility and allow predictions to exist independently if contextual data is unavailable. The ON DELETE SET NULL constraint ensures predictions are preserved even if referenced weather or PAGASA records are deleted, prioritizing data retention over strict referential integrity.

## ✅ Success Criteria

Migration is successful when:
- [x] All SQL statements execute without errors
- [x] Data counts match pre-migration counts
- [x] 90%+ predictions have `weather_data_id` populated
- [x] 80%+ predictions have `pagasa_status_id` populated (some dates may not have PAGASA alerts)
- [x] View `prediction_with_context` returns data
- [x] Existing GitHub Actions workflow runs successfully
- [x] Dashboard loads predictions correctly

## 🆘 Need Help?

If you encounter issues:
1. Check Supabase logs in Dashboard → Logs
2. Run verification queries above
3. Check if foreign key constraints exist: `\d daily_predictions` (in SQL Editor)
4. Worst case: Run rollback script and retry

---

**Next Steps After Migration:**
1. ✅ Run migration script
2. ✅ Execute linking functions
3. ✅ Verify with queries
4. ✅ Update thesis documentation
5. ✅ (Optional) Update `supabase_client.py` for explicit linking
6. ✅ Monitor for 24 hours
