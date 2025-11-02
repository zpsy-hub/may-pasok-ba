# Quick Start Guide

## Current Status

**Notebook:** `01_create_master_dataset.ipynb`  
**Completion:** Phase 1 Complete (13/30+ cells)  
**Ready to Run:** Yes (Phase 1 only)

## What's Been Implemented

### ✅ Phase 1: Foundation (Cells 1-13)
- Setup and configuration
- Data quality gate (LGU standardization, flood risk data)
- Calendar generation (1,100 days, NO weather)
- Cartesian product (18,700 rows)
- Suspension processing and merging
- Validation and output

**Output:** `phase1_master_dataset.csv` (18,700 rows, ~15 columns)

## How to Run Phase 1

### Prerequisites
```bash
# Navigate to notebooks directory
cd model-training/notebooks

# Ensure data files exist:
# - ../data/raw/suspension_data_cleaned.csv
# - ../data/raw/holidays.csv
# - ../data/raw/school_days.csv
# (flood_risk_scores.csv will be created by Cell 4)
```

### Execute
```bash
# Option 1: Jupyter Notebook
jupyter notebook 01_create_master_dataset.ipynb
# Run cells 1-13

# Option 2: JupyterLab
jupyter lab 01_create_master_dataset.ipynb
# Run cells 1-13

# Option 3: VS Code
# Open notebook in VS Code
# Run cells 1-13
```

### Expected Output
After running Cell 13:
```
File created: ../data/processed/phase1_master_dataset.csv
Rows: 18,700
Columns: ~15
Size: ~3-5 MB
```

## What Happens in Each Cell

| Cell | Action | Output |
|------|--------|--------|
| 1 | Import libraries | Success message |
| 2 | Set constants | Configuration summary |
| 3 | Define LGU mapping | 17 LGU names printed |
| 4 | Create flood risk CSV | flood_risk_scores.csv |
| 5 | LGU standardization function | Test cases validated |
| 6 | Load all input CSVs | Validation summary |
| 7 | Generate calendar | 1,100 days with temporal features |
| 8 | Merge holidays/school days | Calendar with flags |
| 9 | Create cartesian product | 18,700-row master dataset |
| 10 | Process suspensions | Target labels assigned |
| 11 | Merge suspensions | Master with target variable |
| 12 | Validate Phase 1 | 8 validation checks |
| 13 | Save Phase 1 output | phase1_master_dataset.csv |

## Validation Checks (Cell 12)

You should see all ✅ PASS:

- [ ] Exactly 18,700 rows (1,100 days × 17 LGUs)
- [ ] Exactly 17 unique LGUs
- [ ] Exactly 1,100 unique dates
- [ ] NO missing values in temporal/flood columns
- [ ] Suspension rate between 3-12%
- [ ] NO one-hot encoding (column count < 30)
- [ ] Correct data types (lgu_id=int, flood_risk=float)
- [ ] lgu_id range is 0-16

## Troubleshooting

### "File not found" errors
**Solution:** Check that input CSVs exist in `../data/raw/`

### "Encoding errors" with ñ
**Solution:** Cell 6 uses `encoding='latin-1'` for suspensions

### "Date parsing errors"
**Solution:** Dates are parsed with specific formats in Cell 6

### "Missing LGU names"
**Solution:** Check that standardization mapping in Cell 5 covers all variants

## Next Steps

After Phase 1 completes successfully:

1. **Review Output:** Check `phase1_master_dataset.csv` 
2. **Verify Schema:** Ensure ~15 columns, no one-hot encoding
3. **Check Suspension Rate:** Should be 5-8%

Then proceed to implement:
- **Phase 2:** Weather data integration (Cells 14-19)
- **Phase 3:** Feature selection (Cells 20-26)
- **Final:** Splits and outputs (Cells 27-30)

## Key Metrics to Expect

```
Total Rows: 18,700
Unique Dates: 1,100
Unique LGUs: 17
Suspension Rate: 5-8%
School Days: ~616
Holidays: ~178
Column Count: 15-18 (NO one-hot)
lgu_id Range: 0-16 (ordinal)
```

## Files Generated

| File | Size | Description |
|------|------|-------------|
| `flood_risk_scores.csv` | <1 KB | 17 LGUs with flood risk scores |
| `phase1_master_dataset.csv` | ~3-5 MB | 18,700 rows, Phase 1 complete |

## Important Notes

1. **NO weather data** in Phase 1 (by design)
2. **lgu_id stays 0-16** (embedding-ready, NO one-hot)
3. **All dates standardized** to YYYY-MM-DD
4. **NCR-wide suspensions** propagated to all 17 LGUs
5. **Validation mandatory** before Phase 2

---

**Ready to Run:** Execute Cells 1-13 sequentially  
**Estimated Time:** 2-5 minutes  
**Requirements:** pandas, numpy, matplotlib, seaborn, scipy, sklearn


