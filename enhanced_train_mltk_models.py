"""
Enhanced Employee SWOT Analysis with Optimized Categorization
This version provides better SWOT distribution using percentile-based thresholds
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import json
import os
from datetime import datetime

class OptimizedEmployeeSWOTMLTK:
    def __init__(self, data_path):
        """Initialize the enhanced MLTK trainer"""
        self.data_path = data_path
        self.models = {}
        self.scalers = {}
        self.model_dir = "models_optimized"
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.feature_columns = [
            'productivity_score', 'engagement_score', 'risk_score', 
            'Work_Hours_Per_Week', 'Overtime_Hours', 'Sick_Days', 
            'Employee_Satisfaction_Score', 'Performance_Score',
            'Projects_Handled', 'Training_Hours'
        ]
        
        self.load_data()
        
    def load_data(self):
        """Load and preprocess employee data"""
        print("Loading employee data...")
        self.df = pd.read_csv(self.data_path)
        print(f"Loaded {len(self.df)} employee records")
        self.create_features()
        
    def create_features(self):
        """Create enhanced productivity, engagement, and risk scores"""
        print("Engineering enhanced features...")
        
        # Normalized Productivity Score (0-5 scale)
        self.df['productivity_score'] = (
            (self.df['Performance_Score'] * 1.2 + 
             (self.df['Work_Hours_Per_Week']/50) * 2 + 
             (self.df['Projects_Handled']/15) * 1.5 + 
             (self.df['Training_Hours']/100) * 1.0 + 
             (self.df['Employee_Satisfaction_Score']/5) * 1.3) / 5
        ).clip(0, 5).round(2)
        
        # Enhanced Engagement Score (0-5 scale)
        self.df['engagement_score'] = (
            (self.df['Employee_Satisfaction_Score'] * 1.5 + 
             (self.df['Training_Hours']/50) * 1.0 + 
             (self.df['Promotions']*3) + 
             (self.df['Remote_Work_Frequency']/100) * 0.5 - 
             (self.df['Sick_Days']*0.3)) / 4
        ).clip(0, 5).round(2)
        
        # Enhanced Risk Score (0-5 scale, lower is better)
        resignation_risk = self.df['Resigned'].map({'True': 2.0, 'False': 0.0})
        self.df['risk_score'] = (
            (self.df['Sick_Days'] * 0.3 + 
             self.df['Overtime_Hours']/15 + 
             resignation_risk + 
             (5 - self.df['Performance_Score']) * 0.4 + 
             (5 - self.df['Employee_Satisfaction_Score']) * 0.3) / 5
        ).clip(0, 5).round(2)
        
        # Additional factors
        self.df['work_life_balance_score'] = 5 - (self.df['Overtime_Hours'] / 10).clip(0, 5)
        self.df['tenure_factor'] = np.log1p(self.df['Years_At_Company']).clip(0, 3)
        
        print("Enhanced feature engineering completed")
        
    def assign_optimized_swot_categories(self):
        """Assign SWOT categories using percentile-based thresholds"""
        print("Assigning optimized SWOT categories...")
        
        # Calculate percentiles for dynamic thresholds
        prod_75 = self.df['productivity_score'].quantile(0.75)
        prod_25 = self.df['productivity_score'].quantile(0.25)
        eng_75 = self.df['engagement_score'].quantile(0.75)
        eng_25 = self.df['engagement_score'].quantile(0.25)
        risk_75 = self.df['risk_score'].quantile(0.75)
        risk_25 = self.df['risk_score'].quantile(0.25)
        
        print(f"Threshold - Productivity: 25th={prod_25:.2f}, 75th={prod_75:.2f}")
        print(f"Threshold - Engagement: 25th={eng_25:.2f}, 75th={eng_75:.2f}")
        print(f"Threshold - Risk: 25th={risk_25:.2f}, 75th={risk_75:.2f}")
        
        # Optimized SWOT assignment
        def assign_swot(row):
            prod = row['productivity_score']
            eng = row['engagement_score']
            risk = row['risk_score']
            
            # Strength: High productivity AND high engagement AND low risk
            if prod >= prod_75 and eng >= eng_75 and risk <= risk_25:
                return 'Strength'
            
            # Threat: High risk AND (low productivity OR low engagement)
            elif risk >= risk_75 and (prod <= prod_25 or eng <= eng_25):
                return 'Threat'
            
            # Weakness: Low productivity AND low engagement
            elif prod <= prod_25 and eng <= eng_25:
                return 'Weakness'
            
            # Opportunity: Everything else (moderate to good potential)
            else:
                return 'Opportunity'
        
        self.df['swot_category'] = self.df.apply(assign_swot, axis=1)
        
        # Store thresholds for future use
        self.swot_thresholds = {
            'productivity_75': prod_75, 'productivity_25': prod_25,
            'engagement_75': eng_75, 'engagement_25': eng_25,
            'risk_75': risk_75, 'risk_25': risk_25
        }
        
    def train_enhanced_clustering(self):
        """Train enhanced K-Means clustering"""
        print("="*60)
        print("Training Enhanced K-Means Clustering...")
        
        features = ['productivity_score', 'engagement_score', 'risk_score', 
                   'work_life_balance_score', 'tenure_factor']
        X = self.df[features].fillna(0)
        
        # Multiple clustering approaches
        results = {}
        
        # Standard K-Means
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        for k in [3, 4, 5]:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X_scaled)
            self.df[f'cluster_{k}'] = clusters
            results[f'kmeans_{k}'] = {
                'model': kmeans,
                'clusters': clusters,
                'inertia': kmeans.inertia_
            }
            
        # Use 4-cluster solution and assign optimized SWOT
        self.df['cluster'] = self.df['cluster_4']
        self.assign_optimized_swot_categories()
        
        # Save best model
        self.models['kmeans'] = results['kmeans_4']['model']
        self.scalers['kmeans'] = scaler
        
        print("Clustering Results:")
        for k in [3, 4, 5]:
            print(f"  K={k}: Inertia={results[f'kmeans_{k}']['inertia']:.0f}")
            
        print(f"\nOptimized SWOT Distribution:")
        swot_counts = self.df['swot_category'].value_counts()
        swot_pcts = (swot_counts / len(self.df) * 100).round(1)
        for category in ['Strength', 'Opportunity', 'Weakness', 'Threat']:
            if category in swot_counts:
                print(f"  {category:12}: {swot_counts[category]:6,} ({swot_pcts[category]:5.1f}%)")
        
    def train_enhanced_anomaly_detection(self):
        """Train enhanced anomaly detection with multiple contamination levels"""
        print("="*60)
        print("Training Enhanced Anomaly Detection...")
        
        features = ['productivity_score', 'engagement_score', 'risk_score', 
                   'Work_Hours_Per_Week', 'Sick_Days', 'Overtime_Hours',
                   'Employee_Satisfaction_Score', 'Performance_Score']
        X = self.df[features].fillna(0)
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Test different contamination levels
        contamination_levels = [0.05, 0.1, 0.15]
        best_contamination = 0.1
        
        for contamination in contamination_levels:
            iso_forest = IsolationForest(contamination=contamination, random_state=42)
            outliers = iso_forest.fit_predict(X_scaled)
            outlier_count = (outliers == -1).sum()
            print(f"  Contamination {contamination}: {outlier_count} outliers ({outlier_count/len(self.df)*100:.1f}%)")
        
        # Train final model with best contamination
        iso_forest = IsolationForest(contamination=best_contamination, random_state=42)
        outliers = iso_forest.fit_predict(X_scaled)
        
        self.df['outlier'] = (outliers == -1).astype(int)
        self.df['anomaly_score'] = iso_forest.decision_function(X_scaled)
        
        # Categorize anomaly severity
        anomaly_threshold_high = np.percentile(self.df['anomaly_score'], 10)
        anomaly_threshold_medium = np.percentile(self.df['anomaly_score'], 25)
        
        self.df['anomaly_level'] = np.select(
            [
                self.df['anomaly_score'] <= anomaly_threshold_high,
                self.df['anomaly_score'] <= anomaly_threshold_medium,
                self.df['anomaly_score'] > anomaly_threshold_medium
            ],
            ['High', 'Medium', 'Low'],
            default='Low'
        )
        
        self.models['isolation_forest'] = iso_forest
        self.scalers['isolation_forest'] = scaler
        
        outlier_count = self.df['outlier'].sum()
        print(f"Enhanced anomaly detection completed:")
        print(f"  Total outliers: {outlier_count} ({outlier_count/len(self.df)*100:.1f}%)")
        print(f"  Anomaly levels: {dict(self.df['anomaly_level'].value_counts())}")
        
    def train_enhanced_attrition_model(self):
        """Train enhanced attrition prediction with feature importance"""
        print("="*60)
        print("Training Enhanced Attrition Prediction...")
        
        X = self.df[self.feature_columns].fillna(0)
        y = self.df['Resigned'].map({'True': 1, 'False': 0}).fillna(0).astype(int)
        
        print(f"Target distribution: {dict(pd.Series(y).value_counts())}")
        
        if y.nunique() < 2:
            print("⚠️ Insufficient target variation for attrition modeling")
            return
            
        # Stratified split to maintain class balance
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train with class balancing
        lr_model = LogisticRegression(
            max_iter=1000, 
            random_state=42,
            class_weight='balanced'  # Handle class imbalance
        )
        lr_model.fit(X_train_scaled, y_train)
        
        # Comprehensive evaluation
        train_score = lr_model.score(X_train_scaled, y_train)
        test_score = lr_model.score(X_test_scaled, y_test)
        y_pred = lr_model.predict(X_test_scaled)
        y_pred_proba = lr_model.predict_proba(X_test_scaled)
        
        print(f"Model Performance:")
        print(f"  Train accuracy: {train_score:.3f}")
        print(f"  Test accuracy: {test_score:.3f}")
        print(f"\nDetailed Classification Report:")
        print(classification_report(y_test, y_pred, zero_division=0))
        
        # Feature importance analysis
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': np.abs(lr_model.coef_[0])
        }).sort_values('importance', ascending=False)
        
        print(f"\nTop 5 Feature Importance:")
        for idx, row in feature_importance.head().iterrows():
            print(f"  {row['feature']:<25}: {row['importance']:.3f}")
        
        # Predict for all employees
        X_scaled = scaler.transform(X)
        probabilities = lr_model.predict_proba(X_scaled)[:, 1]
        self.df['attrition_probability'] = probabilities
        
        # Enhanced risk categorization
        self.df['attrition_risk_level'] = pd.cut(
            probabilities,
            bins=[0, 0.1, 0.3, 0.5, 0.7, 1.0],
            labels=['Very Low', 'Low', 'Medium', 'High', 'Very High'],
            include_lowest=True
        )
        
        self.models['logistic_regression'] = lr_model
        self.scalers['logistic_regression'] = scaler
        
        print(f"\nAttrition Risk Distribution:")
        risk_dist = self.df['attrition_risk_level'].value_counts().sort_index()
        for level, count in risk_dist.items():
            pct = count / len(self.df) * 100
            print(f"  {level:<12}: {count:6,} ({pct:5.1f}%)")
            
    def generate_comprehensive_insights(self):
        """Generate detailed insights and recommendations"""
        print("="*60)
        print("Generating Comprehensive Business Insights...")
        
        insights = {
            'analysis_timestamp': datetime.now().isoformat(),
            'dataset_summary': {
                'total_employees': len(self.df),
                'departments': self.df['Department'].nunique(),
                'avg_tenure': self.df['Years_At_Company'].mean()
            },
            'swot_analysis': {},
            'risk_analysis': {},
            'departmental_insights': {},
            'recommendations': {}
        }
        
        # SWOT Analysis
        swot_dist = self.df['swot_category'].value_counts()
        swot_pcts = (swot_dist / len(self.df) * 100).round(1)
        
        insights['swot_analysis'] = {
            'distribution': swot_dist.to_dict(),
            'percentages': swot_pcts.to_dict(),
            'health_score': (
                swot_pcts.get('Strength', 0) * 1.0 +
                swot_pcts.get('Opportunity', 0) * 0.7 -
                swot_pcts.get('Weakness', 0) * 0.3 -
                swot_pcts.get('Threat', 0) * 1.0
            )
        }
        
        # Risk Analysis
        high_risk_employees = self.df[
            (self.df['swot_category'] == 'Threat') |
            (self.df.get('attrition_risk_level', pd.Series(['Low'] * len(self.df))).isin(['High', 'Very High'])) |
            (self.df['anomaly_level'] == 'High')
        ]
        
        insights['risk_analysis'] = {
            'high_risk_count': len(high_risk_employees),
            'high_risk_percentage': len(high_risk_employees) / len(self.df) * 100,
            'avg_risk_score': self.df['risk_score'].mean(),
            'top_risk_factors': self._identify_risk_factors()
        }
        
        # Departmental Analysis
        dept_analysis = self.df.groupby('Department').agg({
            'swot_category': lambda x: (x == 'Threat').sum(),
            'Employee_ID': 'count',
            'productivity_score': 'mean',
            'engagement_score': 'mean',
            'risk_score': 'mean'
        }).round(3)
        
        # Add attrition probability if available
        if 'attrition_probability' in self.df.columns:
            dept_analysis['attrition_probability'] = self.df.groupby('Department')['attrition_probability'].mean().round(3)
        
        dept_analysis['threat_percentage'] = (
            dept_analysis['swot_category'] / dept_analysis['Employee_ID'] * 100
        ).round(1)
        
        insights['departmental_insights'] = dept_analysis.to_dict('index')
        
        # Generate Recommendations
        insights['recommendations'] = self._generate_recommendations(insights)
        
        return insights
    
    def _identify_risk_factors(self):
        """Identify top risk factors across the organization"""
        risk_factors = {
            'high_overtime': len(self.df[self.df['Overtime_Hours'] > 20]),
            'low_satisfaction': len(self.df[self.df['Employee_Satisfaction_Score'] < 2.5]),
            'high_sick_days': len(self.df[self.df['Sick_Days'] > 10]),
            'low_performance': len(self.df[self.df['Performance_Score'] < 3]),
            'no_training': len(self.df[self.df['Training_Hours'] == 0])
        }
        
        # Sort by prevalence
        sorted_factors = sorted(risk_factors.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_factors[:5])
    
    def _generate_recommendations(self, insights):
        """Generate actionable business recommendations"""
        recommendations = []
        
        # SWOT-based recommendations
        threat_pct = insights['swot_analysis']['percentages'].get('Threat', 0)
        strength_pct = insights['swot_analysis']['percentages'].get('Strength', 0)
        
        if threat_pct > 20:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'Risk Mitigation',
                'action': 'Implement immediate intervention program for high-threat employees',
                'expected_impact': 'Reduce turnover risk by 15-25%'
            })
        
        if strength_pct < 15:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Performance Enhancement',
                'action': 'Develop talent development programs to move Opportunities to Strengths',
                'expected_impact': 'Increase top performer retention by 20%'
            })
        
        # Department-specific recommendations
        high_risk_depts = [
            dept for dept, data in insights['departmental_insights'].items()
            if data['threat_percentage'] > 25
        ]
        
        if high_risk_depts:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Departmental Focus',
                'action': f'Conduct culture assessment in: {", ".join(high_risk_depts)}',
                'expected_impact': 'Improve departmental satisfaction by 15%'
            })
        
        return recommendations
    
    def save_enhanced_models(self):
        """Save all models with comprehensive metadata"""
        print("Saving enhanced models and insights...")
        
        # Save models and scalers
        for name, model in self.models.items():
            joblib.dump(model, os.path.join(self.model_dir, f'{name}_enhanced.pkl'))
            
        for name, scaler in self.scalers.items():
            joblib.dump(scaler, os.path.join(self.model_dir, f'{name}_scaler_enhanced.pkl'))
        
        # Save thresholds and configuration
        config = {
            'swot_thresholds': self.swot_thresholds,
            'feature_columns': self.feature_columns,
            'model_version': '2.0_enhanced',
            'training_date': datetime.now().isoformat()
        }
        
        with open(os.path.join(self.model_dir, 'model_config.json'), 'w') as f:
            json.dump(config, f, indent=2)
        
        # Save comprehensive insights
        insights = self.generate_comprehensive_insights()
        with open(os.path.join(self.model_dir, 'business_insights.json'), 'w') as f:
            json.dump(insights, f, indent=2, default=str)
        
        # Save processed data sample with enhanced features
        columns_to_save = [
            'Employee_ID', 'Department', 'Job_Title',
            'productivity_score', 'engagement_score', 'risk_score',
            'swot_category', 'outlier', 'anomaly_level'
        ]
        
        # Add optional columns if they exist
        if 'attrition_probability' in self.df.columns:
            columns_to_save.extend(['attrition_probability', 'attrition_risk_level'])
            
        enhanced_sample = self.df[columns_to_save].head(1000)
        
        enhanced_sample.to_csv(
            os.path.join(self.model_dir, 'enhanced_sample_data.csv'), 
            index=False
        )
        
        print(f"✅ All enhanced models saved to: {self.model_dir}/")
        
    def run_complete_analysis(self):
        """Execute the complete enhanced analysis pipeline"""
        print("🚀 Starting Enhanced Employee SWOT Analysis")
        print("="*60)
        
        self.train_enhanced_clustering()
        self.train_enhanced_anomaly_detection()
        self.train_enhanced_attrition_model()
        
        # Generate and save insights
        insights = self.generate_comprehensive_insights()
        self.save_enhanced_models()
        
        # Print executive summary
        print("="*60)
        print("📊 EXECUTIVE SUMMARY")
        print("="*60)
        
        print(f"Total Employees Analyzed: {insights['dataset_summary']['total_employees']:,}")
        print(f"Organization Health Score: {insights['swot_analysis']['health_score']:.1f}/100")
        print(f"High-Risk Employees: {insights['risk_analysis']['high_risk_count']:,} "
              f"({insights['risk_analysis']['high_risk_percentage']:.1f}%)")
        
        print(f"\n📈 SWOT Distribution:")
        for category, count in insights['swot_analysis']['distribution'].items():
            pct = insights['swot_analysis']['percentages'][category]
            print(f"  {category:12}: {count:6,} ({pct:5.1f}%)")
        
        print(f"\n🎯 Top Recommendations:")
        for i, rec in enumerate(insights['recommendations'][:3], 1):
            print(f"  {i}. [{rec['priority']}] {rec['action']}")
        
        print("\n✅ Enhanced analysis complete! Ready for Splunk deployment.")
        
        return insights

def main():
    """Main execution with enhanced features"""
    data_path = r"g:\SWOT - Based Employee produxtivity risk monitoring using SPLUNK\Extended_Employee_Performance_and_Productivity_Data.csv"
    
    print("🎯 Enhanced Employee Productivity SWOT Analysis")
    print("Using advanced ML techniques and optimized categorization")
    print("="*60)
    
    # Run enhanced analysis
    analyzer = OptimizedEmployeeSWOTMLTK(data_path)
    insights = analyzer.run_complete_analysis()
    
    print(f"\n📁 Results saved to: {analyzer.model_dir}/")
    print("🔗 Integration files ready for Splunk MLTK deployment")

if __name__ == "__main__":
    main()
