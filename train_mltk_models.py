
"""
Employee Productivity SWOT Analysis - MLTK Model Training Script
This script sets up and trains the MLTK models for employee productivity monitoring
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

class EmployeeSWOTMLTK:
    def __init__(self, data_path):
        """Initialize the MLTK trainer with employee data"""
        self.data_path = data_path
        self.models = {}
        self.scalers = {}
        self.model_dir = "models"
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Define feature columns for different models
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
        
        # Feature Engineering
        self.create_features()
        
    def create_features(self):
        """Create productivity, engagement, and risk scores"""
        print("Engineering features...")
        
        # Productivity Score
        self.df['productivity_score'] = (
            (self.df['Performance_Score'] * 2 + 
             (self.df['Work_Hours_Per_Week']/40) + 
             (self.df['Projects_Handled']/10) + 
             (self.df['Training_Hours']/50) - 
             (self.df['Sick_Days']/5) + 
             (self.df['Employee_Satisfaction_Score']/5)) / 6
        ).round(2)
        
        # Engagement Score
        self.df['engagement_score'] = (
            (self.df['Employee_Satisfaction_Score'] + 
             (self.df['Training_Hours']/10) + 
             (self.df['Promotions']*2) - 
             (self.df['Sick_Days']*0.5)) / 4
        ).round(2)
        
        # Risk Score
        self.df['risk_score'] = (
            (self.df['Sick_Days'] + 
             self.df['Overtime_Hours']/10 + 
             (self.df['Resigned'].map({'True': 5, 'False': 0})) + 
             (5 - self.df['Performance_Score']) - 
             self.df['Employee_Satisfaction_Score']) / 5
        ).round(2)
        
        # Work-life balance score
        self.df['work_life_balance_score'] = self.df['Overtime_Hours'].apply(
            lambda x: 5 if x <= 5 else 4 if x <= 15 else 3 if x <= 25 else 2
        )
        
        # Tenure factor
        self.df['tenure_factor'] = self.df['Years_At_Company'].apply(
            lambda x: 1 if x <= 1 else 2 if x <= 3 else 3 if x <= 5 else 4
        )
        
        print("Feature engineering completed")
        
    def train_clustering_model(self):
        """Train K-Means clustering for SWOT categorization"""
        print("="*50)
        print("Training K-Means clustering model...")
        
        features = ['productivity_score', 'engagement_score', 'risk_score', 
                   'work_life_balance_score', 'tenure_factor']
        X = self.df[features].fillna(0)
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train K-Means with 4 clusters (for SWOT categories)
        kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        
        self.df['cluster'] = clusters
        
        # Assign SWOT categories based on cluster characteristics
        self.assign_swot_categories()
        
        # Save model and scaler
        self.models['kmeans'] = kmeans
        self.scalers['kmeans'] = scaler
        
        print(f"Clustering completed. Cluster distribution:")
        print(self.df['cluster'].value_counts().sort_index())
        print(f"SWOT distribution:")
        print(self.df['swot_category'].value_counts())
        
    def assign_swot_categories(self):
        """Assign SWOT categories based on cluster analysis"""
        cluster_stats = self.df.groupby('cluster').agg({
            'productivity_score': 'mean',
            'engagement_score': 'mean', 
            'risk_score': 'mean'
        })
        
        # Calculate overall averages
        avg_productivity = self.df['productivity_score'].mean()
        avg_engagement = self.df['engagement_score'].mean()
        avg_risk = self.df['risk_score'].mean()
        
        # Assign SWOT categories based on cluster performance vs averages
        swot_mapping = {}
        for cluster in range(4):
            prod = cluster_stats.loc[cluster, 'productivity_score']
            eng = cluster_stats.loc[cluster, 'engagement_score']
            risk = cluster_stats.loc[cluster, 'risk_score']
            
            if prod > avg_productivity and eng > avg_engagement and risk < avg_risk:
                swot_mapping[cluster] = 'Strength'
            elif prod < avg_productivity and eng < avg_engagement:
                swot_mapping[cluster] = 'Weakness'
            elif risk > avg_risk and (prod < avg_productivity or eng < avg_engagement):
                swot_mapping[cluster] = 'Threat'
            else:
                swot_mapping[cluster] = 'Opportunity'
        
        self.df['swot_category'] = self.df['cluster'].map(swot_mapping)
        self.swot_mapping = swot_mapping
        
    def train_anomaly_detection(self):
        """Train Isolation Forest for anomaly detection"""
        print("="*50)
        print("Training anomaly detection model...")
        
        features = ['productivity_score', 'engagement_score', 'risk_score', 
                   'Work_Hours_Per_Week', 'Sick_Days', 'Overtime_Hours']
        X = self.df[features].fillna(0)
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train Isolation Forest
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        outliers = iso_forest.fit_predict(X_scaled)
        
        self.df['outlier'] = (outliers == -1).astype(int)
        
        # Save model and scaler
        self.models['isolation_forest'] = iso_forest
        self.scalers['isolation_forest'] = scaler
        
        outlier_count = self.df['outlier'].sum()
        print(f"Anomaly detection completed. Found {outlier_count} outliers ({outlier_count/len(self.df)*100:.1f}%)")
        
    def train_attrition_model(self):
        """Train logistic regression for attrition prediction"""
        print("="*50)
        print("Training attrition prediction model...")

        # Extract features and target
        X = self.df[self.feature_columns].fillna(0)
        y_raw = self.df['Resigned']

        # Convert True/False or string to integer (binary classification: 1 = Resigned)
        y = y_raw.astype(str).str.lower().map({'true': 1, 'false': 0}).fillna(0).astype(int)

        # ⚠️ Check for at least 2 classes in target
        unique_classes = y.nunique()
        if unique_classes < 2:
            print(f"⚠️ Skipping attrition model training: only one class present in 'Resigned' column ({y.unique()}).")
            return

        # Continue with training if classes are valid
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        lr_model = LogisticRegression(max_iter=1000, random_state=42)
        lr_model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        y_pred = lr_model.predict(X_test_scaled)
        train_score = lr_model.score(X_train_scaled, y_train)
        test_score = lr_model.score(X_test_scaled, y_test)
        
        print("Attrition Model Evaluation:")
        print(f"Train accuracy: {train_score:.3f}")
        print(f"Test accuracy: {test_score:.3f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        # Predict probabilities for all data
        X_scaled = scaler.transform(X)
        self.df['attrition_probability'] = lr_model.predict_proba(X_scaled)[:, 1]
        self.df['attrition_risk_level'] = self.df['attrition_probability'].apply(
            lambda x: 'Very High' if x > 0.7 else 'High' if x > 0.5 else 'Medium' if x > 0.3 else 'Low' if x > 0.1 else 'Very Low'
        )

        # Save the model and scaler
        self.models['logistic_regression'] = lr_model
        self.scalers['logistic_regression'] = scaler
        
        print(f"\nAttrition risk distribution:")
        print(self.df['attrition_risk_level'].value_counts())
        print("Attrition prediction model training completed.")

    def generate_insights(self):
        """Generate comprehensive insights from the models"""
        print("Generating insights...")
        
        insights = {
            'timestamp': datetime.now().isoformat(),
            'total_employees': len(self.df),
            'swot_distribution': self.df['swot_category'].value_counts().to_dict(),
            'department_risks': {},
            'high_risk_employees': [],
            'model_performance': {}
        }
        
        # Department-wise analysis
        dept_analysis = self.df.groupby('Department').agg({
            'swot_category': lambda x: (x == 'Threat').sum(),
            'Employee_ID': 'count',
            'productivity_score': 'mean',
            'engagement_score': 'mean',
            'risk_score': 'mean'
        }).round(2)
        
        dept_analysis['threat_percentage'] = (dept_analysis['swot_category'] / dept_analysis['Employee_ID'] * 100).round(1)
        insights['department_risks'] = dept_analysis.to_dict('index')
        
        # High risk employees
        if 'attrition_risk_level' in self.df.columns:
            high_risk = self.df[
                (self.df['swot_category'] == 'Threat') | 
                (self.df['attrition_risk_level'].isin(['Very High', 'High']))
            ][['Employee_ID', 'Department', 'Job_Title', 'swot_category', 'attrition_risk_level', 
               'productivity_score', 'engagement_score', 'risk_score']].to_dict('records')
            
            insights['high_risk_employees'] = high_risk[:20]  # Top 20 high-risk employees
        
        return insights
        
    def save_models(self):
        """Save trained models and metadata"""
        # Save models
        for model_name, model in self.models.items():
            joblib.dump(model, os.path.join(self.model_dir, f'{model_name}.pkl'))
            print(f"Saved {model_name} model")
            
        # Save scalers
        for scaler_name, scaler in self.scalers.items():
            joblib.dump(scaler, os.path.join(self.model_dir, f'{scaler_name}_scaler.pkl'))
            print(f"Saved {scaler_name} scaler")
            
        # Save SWOT mapping
        if hasattr(self, 'swot_mapping'):
            with open(os.path.join(self.model_dir, 'swot_mapping.json'), 'w') as f:
                json.dump(self.swot_mapping, f, indent=2)
                
        # Save processed data sample
        sample_data = self.df.head(1000).to_csv(os.path.join(self.model_dir, 'sample_processed_data.csv'), index=False)
        print(f"Saved sample processed data")
        
        # Save insights
        insights = self.generate_insights()
        with open(os.path.join(self.model_dir, 'model_insights.json'), 'w') as f:
            json.dump(insights, f, indent=2, default=str)
            
        print(f"All models and artifacts saved to {self.model_dir}/")
        
    def train_all_models(self):
        """Train all MLTK models"""
        print("Starting comprehensive model training...")
        print("="*50)
        
        # Train all models
        self.train_clustering_model()
        self.train_anomaly_detection()
        self.train_attrition_model()
        
        # Save everything
        self.save_models()
        
        print("="*50)
        print("Model training completed successfully!")
        
        # Print summary
        print("\nModel Training Summary:")
        print(f"Total employees processed: {len(self.df)}")
        print(f"SWOT Categories: {dict(self.df['swot_category'].value_counts())}")
        print(f"High-risk employees: {len(self.df[self.df['swot_category'] == 'Threat'])}")
        print(f"Anomalies detected: {self.df['outlier'].sum()}")
        if 'attrition_risk_level' in self.df.columns:
            print(f"High attrition risk: {len(self.df[self.df['attrition_risk_level'].isin(['Very High', 'High'])])}")

def main():
    """Main execution function"""
    data_path = r"g:\SWOT - Based Employee produxtivity risk monitoring using SPLUNK\Extended_Employee_Performance_and_Productivity_Data.csv"
    
    # Initialize and train models
    trainer = EmployeeSWOTMLTK(data_path)
    trainer.train_all_models()
    
    print("\nTraining completed! Models are ready for deployment in Splunk MLTK.")
    print("Next steps:")
    print("1. Copy model files to Splunk MLTK model directory")
    print("2. Import saved searches and dashboard configurations")
    print("3. Configure alerts and notifications")
    print("4. Test the complete SWOT monitoring solution")

if __name__ == "__main__":
    main()

