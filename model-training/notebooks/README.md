# Master Dataset Creation Notebook

## Status

**Notebook:** `01_create_master_dataset.ipynb`

**Current Implementation Status:** Phase 1 - In Progress

## Completed Sections

### Section 0: Setup & Configuration (Cells 1-3) ✅
- Library imports (pandas, numpy, sklearn, statsmodels)
- Constants and random seed configuration
- LOCATION_MAPPING with 17 canonical LGU names
- File path definitions

### Section 1: Data Quality Gate (Cells 4-6) ✅
- **Cell 4:** Created flood_risk_scores.csv from Siddayao et al. (2020) data
- **Cell 5:** LGU name standardization function (handles "City" suffix, ñ encoding)
- **Cell 6:** Loaded and validated all input CSVs (suspensions, holidays, school_days, flood_risk)

## Remaining Implementation

### Section 2: PHASE 1 - Calendar Foundation (Cells 7-9)
- **Cell 7:** Generate 1,100-day calendar with temporal features (NO weather data)
- **Cell 8:** Merge holidays and school days
- **Cell 9:** EDA - Calendar summary statistics

### Section 3: PHASE 1 - Cartesian Product & Geography (Cells 10-11)
- **Cell 10:** Create 18,700-row dataset (date × 17 LGUs)
- **Cell 11:** EDA - Geography distribution

### Section 4: PHASE 1 - Suspension Target Processing (Cells 12-14)
- **Cell 12:** Process suspension data (BAGYO/HABAGAT/ULAN = 1)
- **Cell 13:** Merge suspensions into master dataset
- **Cell 14:** EDA - Suspension patterns

### Section 5: PHASE 1 - Validation & Output (Cells 15-16)
- **Cell 15:** Phase 1 validation checks
- **Cell 16:** Save Phase 1 master dataset

### Section 6: PHASE 2 - Weather Data Integration (Cells 17-22)
- **Cell 17:** Load weather data (actual and forecast)
- **Cell 18:** Engineer weather features with TEMPORAL LAG (t-1 only)
- **Cell 19:** Anti-leakage validation for weather features
- **Cell 20:** Merge weather features onto Phase 1 master
- **Cell 21:** EDA - Weather feature distributions
- **Cell 22:** EDA - Weather vs suspensions

### Section 7: PHASE 3 - Feature Selection Protocol (Cells 23-30)
- **Cell 23:** Calculate maximum safe feature count (EPV)
- **Cell 24:** Stage 2.1 - Remove non-predictive features
- **Cell 25:** Stage 2.2 - Remove redundant features
- **Cell 26:** Stage 2.3 - Permutation importance
- **Cell 27:** Stage 2.3 cont. - Iterative feature pruning
- **Cell 28:** Stage 2.4 - Recursive Feature Elimination (optional)
- **Cell 29:** Post-selection EDA and validation
- **Cell 30:** Document feature lineage

### Section 8: Train/Validation/Test Splits (Cells 31-33)
- **Cell 31:** Create chronological splits
- **Cell 32:** Validate split safety
- **Cell 33:** EDA - Split comparison

### Section 9: Final Outputs & Validation (Cells 34-36)
- **Cell 34:** Save all output files
- **Cell 35:** Final comprehensive validation
- **Cell 36:** Anti-leakage audit summary

## Expected Outputs

1. **phase1_master_dataset.csv** - 18,700 rows, Phase 1 complete
2. **master_dataset_ready_for_training.csv** - Phase 2 complete with weather features
3. **master_train.csv** - Training split (2022-08-22 to 2024-05-31)
4. **master_validation.csv** - Validation split (2024-06-01 to 2024-11-30)
5. **master_test.csv** - Test split (2024-12-01 to 2025-08-25)
6. **split_metadata.json** - Reproducibility documentation

## Key References

- `ml_weather_pipeline_master.md` - Anti-leakage protocol
- `feature_selection_protocol.md` - Feature selection methodology
- `cursor_final_instructions.md` - Dataset specifications

## Next Steps

1. Complete Phase 1 calendar generation (Cells 7-9)
2. Build cartesian product (Cells 10-11)
3. Process and merge suspensions (Cells 12-14)
4. Validate Phase 1 and save intermediate output (Cells 15-16)
5. Integrate weather data with temporal lag (Phase 2)
6. Apply feature selection protocol (Phase 3)
7. Create and validate splits
8. Generate final outputs

## Notes

- All features must respect temporal lag (t-1)
- NO one-hot encoding (use numeric ordinal)
- lgu_id stays as 0-16 integer (embedding-ready)
- Strict anti-leakage validation at every stage
- Comprehensive EDA after each phase
