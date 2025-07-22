# Employee Productivity SWOT Analysis - Core Searches and MLTK Models

## 1. Data Preparation and Feature Engineering
### Base Search for Employee Metrics
search_name: employee_base_metrics
```spl
index=employee_productivity sourcetype=csv
| eval productivity_score = round((performance_score * 2 + (work_hours_per_week/40) + (projects_handled/10) + (training_hours/50) - (sick_days/5) + (employee_satisfaction_score/5)) / 6, 2)
| eval engagement_score = round((employee_satisfaction_score + (training_hours/10) + (promotions*2) - (sick_days*0.5)) / 4, 2)
| eval risk_score = round((sick_days + overtime_hours/10 + if(resigned=="True", 5, 0) + (5-performance_score) - (employee_satisfaction_score)) / 5, 2)
| eval work_life_balance_score = case(overtime_hours <= 5, 5, overtime_hours <= 15, 4, overtime_hours <= 25, 3, overtime_hours > 25, 2)
| eval tenure_factor = case(years_at_company <= 1, 1, years_at_company <= 3, 2, years_at_company <= 5, 3, years_at_company > 5, 4)
| table employee_id, department, age, performance_score, productivity_score, engagement_score, risk_score, work_life_balance_score, tenure_factor, work_hours_per_week, projects_handled, training_hours, sick_days, overtime_hours, remote_work_frequency, employee_satisfaction_score, resigned
```

## 2. MLTK Clustering for SWOT Categories
### K-Means Clustering Model
search_name: employee_clustering_model
```spl
| `employee_base_metrics`
| fit KMeans productivity_score engagement_score risk_score work_life_balance_score tenure_factor k=4 into employee_swot_clusters
```

### Apply Clustering and Assign SWOT Categories
search_name: employee_swot_assignment
```spl
| `employee_base_metrics`
| apply employee_swot_clusters
| eval cluster_interpretation = case(
    cluster == 0, "analyze_cluster_0",
    cluster == 1, "analyze_cluster_1", 
    cluster == 2, "analyze_cluster_2",
    cluster == 3, "analyze_cluster_3"
)
| eventstats avg(productivity_score) as avg_productivity, avg(engagement_score) as avg_engagement, avg(risk_score) as avg_risk by cluster
| eval swot_category = case(
    productivity_score > avg_productivity AND engagement_score > avg_engagement AND risk_score < avg_risk, "Strength",
    productivity_score < avg_productivity AND engagement_score < avg_engagement, "Weakness", 
    risk_score > avg_risk AND (productivity_score < avg_productivity OR engagement_score < avg_engagement), "Threat",
    (productivity_score >= avg_productivity OR engagement_score >= avg_engagement) AND risk_score <= avg_risk, "Opportunity"
)
| table employee_id, department, swot_category, cluster, productivity_score, engagement_score, risk_score, performance_score, employee_satisfaction_score
```

## 3. Anomaly Detection for Early Warning
### Isolation Forest for Anomaly Detection
search_name: employee_anomaly_detection
```spl
| `employee_base_metrics`
| fit IsolationForest productivity_score engagement_score risk_score work_hours_per_week sick_days overtime_hours into employee_anomaly_model
| apply employee_anomaly_model
| where outlier == 1
| eval alert_level = case(
    risk_score >= 4, "Critical",
    risk_score >= 3, "High", 
    risk_score >= 2, "Medium",
    1==1, "Low"
)
| table employee_id, department, swot_category, alert_level, productivity_score, engagement_score, risk_score, outlier
```

## 4. Time Series Analysis for Trend Detection
### Note: This requires time-series data simulation since our dataset is snapshot-based
search_name: employee_trend_simulation
```spl
| `employee_base_metrics`
| eval trend_direction = case(
    years_at_company <= 1 AND performance_score >= 4, "upward",
    years_at_company > 3 AND performance_score <= 2, "downward",
    performance_score >= 3, "stable",
    1==1, "concerning"
)
| eval trend_strength = case(
    trend_direction == "upward" AND productivity_score > 3.5, "strong",
    trend_direction == "downward" AND risk_score > 3, "strong", 
    1==1, "moderate"
)
| table employee_id, department, trend_direction, trend_strength, swot_category
```

## 5. Real-time Monitoring and Alerting
### SWOT Category Movement Detection
search_name: swot_category_changes
```spl
| `employee_swot_assignment`
| eval previous_swot = "Opportunity"  # This would come from previous runs in real implementation
| where swot_category != previous_swot
| eval change_type = case(
    previous_swot == "Strength" AND swot_category == "Threat", "Critical_Decline",
    previous_swot == "Opportunity" AND swot_category == "Strength", "Positive_Growth",
    previous_swot == "Weakness" AND swot_category == "Threat", "Escalating_Risk",
    swot_category == "Threat", "New_Threat",
    1==1, "Category_Change"
)
| table employee_id, department, previous_swot, swot_category, change_type, alert_level
```

## 6. Departmental Risk Assessment
### Department-wise SWOT Distribution
search_name: department_swot_analysis
```spl
| `employee_swot_assignment`
| stats 
    count as total_employees,
    count(eval(swot_category=="Strength")) as strengths,
    count(eval(swot_category=="Weakness")) as weaknesses, 
    count(eval(swot_category=="Opportunity")) as opportunities,
    count(eval(swot_category=="Threat")) as threats,
    avg(productivity_score) as avg_productivity,
    avg(engagement_score) as avg_engagement,
    avg(risk_score) as avg_risk
    by department
| eval strength_pct = round((strengths/total_employees)*100, 2)
| eval threat_pct = round((threats/total_employees)*100, 2)
| eval department_risk_level = case(
    threat_pct > 25, "High Risk",
    threat_pct > 15, "Medium Risk", 
    threat_pct > 5, "Low Risk",
    1==1, "Minimal Risk"
)
| sort - threat_pct
```

## 7. Predictive Analytics for Attrition Risk
### Logistic Regression for Resignation Prediction
search_name: attrition_prediction_model
```spl
| `employee_base_metrics`
| eval resigned_binary = if(resigned=="True", 1, 0)
| fit LogisticRegression resigned_binary from productivity_score engagement_score risk_score work_hours_per_week overtime_hours sick_days employee_satisfaction_score into employee_attrition_model
```

### Apply Attrition Prediction
search_name: attrition_risk_scoring
```spl
| `employee_base_metrics`
| apply employee_attrition_model
| eval attrition_probability = round(predicted_resigned_binary, 3)
| eval attrition_risk_level = case(
    attrition_probability > 0.7, "Very High",
    attrition_probability > 0.5, "High",
    attrition_probability > 0.3, "Medium", 
    attrition_probability > 0.1, "Low",
    1==1, "Very Low"
)
| table employee_id, department, swot_category, attrition_probability, attrition_risk_level, productivity_score, engagement_score, risk_score
```

## 8. Comprehensive Employee Risk Dashboard Query
search_name: comprehensive_employee_dashboard
```spl
| `employee_swot_assignment`
| lookup employee_attrition_model employee_id OUTPUT attrition_probability, attrition_risk_level
| eval overall_risk = case(
    swot_category == "Threat" AND attrition_risk_level == "Very High", "Critical",
    swot_category == "Threat" OR attrition_risk_level == "High", "High",
    swot_category == "Weakness" AND attrition_risk_level == "Medium", "Medium",
    1==1, "Low"
)
| eval recommendation = case(
    overall_risk == "Critical", "Immediate intervention required - Schedule urgent 1-on-1",
    overall_risk == "High", "Weekly check-ins and support review needed",
    overall_risk == "Medium", "Monthly monitoring and career development discussion",
    swot_category == "Opportunity", "Consider for promotion or expanded responsibilities",
    1==1, "Continue standard management practices"
)
| table employee_id, department, job_title, swot_category, overall_risk, attrition_risk_level, productivity_score, engagement_score, risk_score, recommendation
```
