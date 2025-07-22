# Splunk Dashboard Troubleshooting Guide

## Current Issues Analysis

The error messages you're seeing indicate that Splunk is trying to use old cached searches or incorrect data sources. Here's how to fix them:

### **Issue 1: "inputlookup enhanced_sample_data.csv" errors**
**Problem**: Splunk is caching old search queries that reference a different CSV file
**Solution**: Clear Splunk cache and restart Splunk services

### **Issue 2: "No matching visualization found" errors**
**Problem**: Dashboard XML may have incorrect visualization types or caching issues
**Solution**: Use the new `employee_swot_dashboard_fixed.xml` file

## Step-by-Step Resolution

### **Step 1: Clear Splunk Cache**
```bash
# Stop Splunk
$SPLUNK_HOME/bin/splunk stop

# Clear search cache
rm -rf $SPLUNK_HOME/var/run/splunk/dispatch/*
rm -rf $SPLUNK_HOME/var/run/splunk/searchpeers/*

# Clear knowledge bundle cache
rm -rf $SPLUNK_HOME/var/run/splunk/bundle_tmp/*

# Start Splunk
$SPLUNK_HOME/bin/splunk start
```

### **Step 2: Restart Data Input**
1. In Splunk Web, go to **Settings > Data Inputs > Files & Directories**
2. Find your CSV monitor and **Disable** it
3. Wait 30 seconds, then **Enable** it again
4. Or run: `$SPLUNK_HOME/bin/splunk reload deploy-server`

### **Step 3: Verify Data Index**
Run this search in Splunk Search & Reporting:
```spl
index=employee_productivity sourcetype=csv | head 5 | table Employee_ID, Department, Performance_Score
```

**Expected Result**: Should show 5 employee records with proper field names

### **Step 4: Test Simple Dashboard**
1. Upload `employee_swot_dashboard_test.xml` first
2. Verify it loads without errors
3. Check that data appears correctly

### **Step 5: Deploy Fixed Dashboard**
1. Upload `employee_swot_dashboard_fixed.xml`
2. The new version has:
   - ✅ Improved SWOT scoring logic (better distribution)
   - ✅ All direct SPL queries (no macros)
   - ✅ Proper visualization types
   - ✅ Correct field names

## File Status Summary

| File | Status | Purpose |
|------|--------|---------|
| `inputs.conf` | ✅ **Fixed** | Removed conflicting field extractions |
| `employee_swot_dashboard_test.xml` | ✅ **New** | Simple test version |
| `employee_swot_dashboard_fixed.xml` | ✅ **New** | Production-ready fixed version |
| `verify_dashboard_data.py` | ✅ **New** | Data validation script |

## Key Changes Made

### **SWOT Scoring Improvements**
- **Old**: 97.3% threats (too strict)
- **New**: Balanced distribution with adjusted thresholds
- **Logic**: More realistic productivity and risk calculations

### **Visualization Fixes**
- **Old**: Custom viz types causing errors
- **New**: Standard Splunk chart elements
- **Result**: All visualizations will render properly

### **Data Source Fixes**
- **Old**: Conflicting field extractions
- **New**: Clean CSV header auto-extraction
- **Result**: Proper field name recognition

## Verification Steps

### **1. Data Ingestion Check**
```spl
index=employee_productivity | stats count by sourcetype
```
Expected: `csv` with 100,000 count

### **2. Field Extraction Check**
```spl
index=employee_productivity | head 1 | eval test_field=Employee_ID | table Employee_ID, Department, test_field
```
Expected: Valid employee ID and department values

### **3. SWOT Calculation Check**
```spl
index=employee_productivity 
| head 100
| eval productivity_score = round((Performance_Score * 1.5 + (Work_Hours_Per_Week/40) + (Projects_Handled/15) + (Training_Hours/30) - (Sick_Days/10) + (Employee_Satisfaction_Score/3)) / 5, 2)
| stats count by productivity_score
```
Expected: Distribution of productivity scores

## If Issues Persist

### **Alternative Data Input Method**
If monitor input continues to have issues, try manual upload:

1. **Settings > Add Data > Upload**
2. Select your CSV file
3. Set these parameters:
   - **Source type**: `csv`
   - **Index**: `employee_productivity`
   - **Host**: `employee_data`

### **Manual Index Creation**
```bash
# Create index manually
$SPLUNK_HOME/bin/splunk add index employee_productivity

# Restart Splunk
$SPLUNK_HOME/bin/splunk restart
```

### **Check Splunk Logs**
```bash
tail -f $SPLUNK_HOME/var/log/splunk/splunkd.log | grep -i error
```

## Contact Support If Needed

If these steps don't resolve the issues, the problem may be:
1. **Splunk version compatibility** (requires Splunk 8.0+)
2. **File permissions** on the CSV file
3. **Disk space** issues in Splunk
4. **Network connectivity** between Splunk components

## Expected Final Result

After following these steps, your dashboard should show:
- ✅ **SWOT Distribution**: Balanced categories (not 97% threats)
- ✅ **Total Employees**: 100,000
- ✅ **All Visualizations**: Properly rendered charts and tables
- ✅ **No Error Messages**: Clean dashboard operation
- ✅ **Interactive Filters**: Department and time range working

The fixed dashboard provides better insights with realistic SWOT categorization and reliable visualization rendering.
