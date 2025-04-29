import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pickle
import os

# Load your dataset
df = pd.read_csv('/Users/agakshita/Desktop/hb_flask2/data/hd.csv')
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

# Create models directory if it doesn't exist
os.makedirs('/Users/agakshita/Desktop/hb_flask2/app/models', exist_ok=True)

# Save the scaler
with open('/Users/agakshita/Desktop/hb_flask2/app/models/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

# Train and save the model
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight='balanced',
    random_state=42
)
model.fit(X_train, y_train)

with open('/Users/agakshita/Desktop/hb_flask2/app/models/heart_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("Model trained and saved successfully!")