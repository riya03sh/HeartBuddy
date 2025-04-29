import pandas as pd
import pickle
import os

class HeartDiseasePredictor:
    def __init__(self):
        # Get the directory of this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Construct paths to model files
        model_path = os.path.join(current_dir, '../models/heart_model.pkl')
        scaler_path = os.path.join(current_dir, '../models/scaler.pkl')
        
        # Load model and scaler
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        with open(scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)
        
        self.numerical_cols = ['age', 'bps', 'chol', 'mhr']

    def predict_risk(self, input_data):
        # Convert input to DataFrame
        input_df = pd.DataFrame([input_data])
        
        # Scale numerical features
        input_df[self.numerical_cols] = self.scaler.transform(input_df[self.numerical_cols])
        
        # Predict
        probability = self.model.predict_proba(input_df)[0][1]
        
        # Risk stratification
        if probability < 0.3:
            risk_level = 'Low'
            color = 'success'
            recommendation = "Keep up the healthy lifestyle!"
        elif probability < 0.7:
            risk_level = 'Medium'
            color = 'warning'
            recommendation = "Consider moderate lifestyle changes and consult a doctor."
        else:
            risk_level = 'High'
            color = 'danger'
            recommendation = "Consult a cardiologist immediately and consider major lifestyle changes."

        return {
            'probability': probability * 100,  # Convert to percentage
            'risk_level': risk_level,
            'color': color,
            'recommendation': recommendation,
            'feature_importance': dict(zip(
                input_df.columns,
                self.model.feature_importances_
            ))
        }

# Create singleton instance
predictor = HeartDiseasePredictor()