#!/usr/bin/env python3
"""
Verification script for Employee SWOT Dashboard
Tests data processing and field calculations
"""

import pandas as pd
import os

def test_data_processing():
    """Test the data processing logic used in the dashboard"""
    
    # Load the CSV file
    csv_path = "Extended_Employee_Performance_and_Productivity_Data.csv"
    
    if not os.path.exists(csv_path):
        print(f"❌ Error: CSV file not found at {csv_path}")
        return False
    
    print("📊 Loading employee data...")
    df = pd.read_csv(csv_path)
    
    print(f"✅ Loaded {len(df)} employee records")
    print(f"📋 Columns: {list(df.columns)}")
    
    # Test basic calculations
    print("\n🧮 Testing SWOT calculations...")
    
    # Calculate productivity score (matching dashboard logic)
    df['productivity_score'] = round(
        (df['Performance_Score'] * 2 + 
         (df['Work_Hours_Per_Week']/40) + 
         (df['Projects_Handled']/10) + 
         (df['Training_Hours']/50) - 
         (df['Sick_Days']/5) + 
         (df['Employee_Satisfaction_Score']/5)) / 6, 2
    )
    
    # Calculate engagement score
    df['engagement_score'] = round(
        (df['Employee_Satisfaction_Score'] + 
         (df['Training_Hours']/10) + 
         (df['Promotions']*2) - 
         (df['Sick_Days']*0.5)) / 4, 2
    )
    
    # Calculate risk score
    df['risk_score'] = round(
        (df['Sick_Days'] + 
         df['Overtime_Hours']/10 + 
         df['Resigned'].apply(lambda x: 5 if x == True or x == 'True' else 0) + 
         (5-df['Performance_Score']) - 
         df['Employee_Satisfaction_Score']) / 5, 2
    )
    
    # SWOT categorization
    def assign_swot(row):
        if (row['productivity_score'] >= 3.5 and 
            row['engagement_score'] >= 3.5 and 
            row['risk_score'] <= 2):
            return "Strength"
        elif (row['productivity_score'] < 2.5 or 
              row['engagement_score'] < 2.5 or 
              row['risk_score'] >= 4):
            return "Threat"
        elif (row['productivity_score'] >= 2.5 and row['productivity_score'] < 3.5 and
              row['engagement_score'] >= 2.5 and row['engagement_score'] < 3.5):
            return "Weakness"
        else:
            return "Opportunity"
    
    df['swot_category'] = df.apply(assign_swot, axis=1)
    
    # Display results
    print("\n📈 SWOT Distribution:")
    swot_counts = df['swot_category'].value_counts()
    swot_percentages = (swot_counts / len(df) * 100).round(2)
    
    for category in ['Strength', 'Weakness', 'Opportunity', 'Threat']:
        count = swot_counts.get(category, 0)
        pct = swot_percentages.get(category, 0)
        print(f"  {category}: {count:,} employees ({pct}%)")
    
    print(f"\n📊 Summary Statistics:")
    print(f"  Average Productivity Score: {df['productivity_score'].mean():.2f}")
    print(f"  Average Engagement Score: {df['engagement_score'].mean():.2f}")
    print(f"  Average Risk Score: {df['risk_score'].mean():.2f}")
    
    # Department breakdown
    print(f"\n🏢 Department Breakdown:")
    dept_stats = df.groupby('Department').agg({
        'Employee_ID': 'count',
        'swot_category': lambda x: (x == 'Threat').sum(),
        'productivity_score': 'mean',
        'risk_score': 'mean'
    }).round(2)
    
    dept_stats.columns = ['Total_Employees', 'Threats', 'Avg_Productivity', 'Avg_Risk']
    dept_stats['Threat_Percentage'] = round((dept_stats['Threats'] / dept_stats['Total_Employees']) * 100, 2)
    
    print(dept_stats.to_string())
    
    # Check for data quality issues
    print(f"\n🔍 Data Quality Check:")
    print(f"  Missing values in key fields:")
    key_fields = ['Employee_ID', 'Department', 'Performance_Score', 'Employee_Satisfaction_Score']
    for field in key_fields:
        missing = df[field].isnull().sum()
        print(f"    {field}: {missing} missing")
    
    print(f"\n✅ Data processing test completed successfully!")
    return True

if __name__ == "__main__":
    try:
        test_data_processing()
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
