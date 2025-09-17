# Non-Migrated Data Summary - SDB Supabase Migration

## Migration Results Overview
- **Total Records**: 802 inscriptions
- **Successfully Migrated**: 598 (74.6%)
- **Non-Migrated**: 204 (25.4%)

## Issue Breakdown
1. **Missing Students**: 179 records (87.7% of issues)
   - Students exist in inscriptions but not in catechumenes table
   - Foreign key constraint violations
   
2. **Missing Classes**: 58 records (28.4% of issues)
   - Class names in Baserow don't match Supabase class names
   - Some classes may not have been created in Supabase
   
3. **Invalid Enum Values**: 53 records (26.0% of issues)
   - Payment methods: "Au Secrétariat", "ORANGE MONEY" (not in enum)
   - Status values: "Inscription Validee" (should be "Inscription Validée")
   - Yes/No fields containing dates instead of boolean values
   
4. **Other Issues**: 3 records (1.5% of issues)
   - Unknown constraint violations

## Main Issues Identified

### 1. Data Integrity Problems
- Many inscriptions reference students that don't exist in the main student table
- This suggests either:
  - Students were deleted from catechumenes but not from inscriptions
  - Data entry errors in student IDs
  - Incomplete initial migration of student data

### 2. Class Name Mismatches
- Baserow class names may not exactly match Supabase class names
- Need to verify class mapping between systems

### 3. Data Format Inconsistencies
- Payment method field contains free-text instead of standardized values
- Some yes/no fields contain date strings instead of boolean values
- Status field has spelling variations

## Recommendations

### Immediate Actions
1. **Data Cleaning Priority**: Fix missing student references (179 records)
2. **Class Mapping**: Verify and correct class name mappings (58 records)
3. **Enum Standardization**: Clean up enum values (53 records)

### Long-term Improvements
1. **Data Validation**: Implement validation rules in Baserow
2. **Referential Integrity**: Regular checks for orphaned records
3. **Standardized Values**: Use dropdowns instead of free-text for enum fields

### Files Generated
- `non_migrated_report.md`: Detailed analysis with individual record issues
- `non_migrated_data.txt`: Raw data for all non-migrated records
- `extract_non_migrated.py`: Script to regenerate this analysis

## Next Steps
1. Review the detailed report for specific records needing attention
2. Clean up data quality issues in Baserow
3. Re-run migration for cleaned records
4. Consider running this analysis periodically to catch data quality issues early

---
*Generated: 2025-09-12 21:42:02*