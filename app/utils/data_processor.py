import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import pickle
import os

def load_and_prepare_data():
    # Load dataset
    df = pd.read_csv('data/hd.csv')
    df = df.rename(columns={
        'trestbps': 'bps',
        'thalachh': 'mhr'
    })
    
    # Prepare features and target
    X = df.drop('target', axis=1)
    y = df['target']
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale numerical features
    numerical_cols = ['age', 'bps', 'chol', 'mhr']
    scaler = StandardScaler()
    X_train[numerical_cols] = scaler.fit_transform(X_train[numerical_cols])
    X_test[numerical_cols] = scaler.transform(X_test[numerical_cols])
    
    # Save scaler
    os.makedirs('app/models', exist_ok=True)
    with open('/Users/agakshita/Desktop/hb_flask/app/models/scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    
    return X_train, X_test, y_train, y_test

def train_and_save_model():
    X_train, X_test, y_train, y_test = load_and_prepare_data()
    
    # Initialize model
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight='balanced',
        random_state=42
    )
    
    # Train model
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    print("Classification Report:")
    print(classification_report(y_test, y_pred))
    print(f"\nAccuracy: {accuracy_score(y_test, y_pred)*100:.2f}%")
    
    # Save model
    with open('/Users/agakshita/Desktop/hb_flask/app/models/heart_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    
    return model