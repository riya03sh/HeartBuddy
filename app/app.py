# app.py - Combined Flask Application
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from datetime import datetime, timezone, timedelta
import pandas as pd
import json
import firebase_admin
from firebase_admin import auth, credentials, firestore
from werkzeug.utils import secure_filename
import os
from utils.model_predictor import predictor

# Initialize Flask Application
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this for production

# Initialize Firebase Admin
def initialize_firebase():
    try:
        # Path to your Firebase service account key
        cred_path = os.path.join(os.path.dirname(__file__), 'firebase', 'serviceAccountKey.json')
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("Firebase Admin initialized successfully")
    except Exception as e:
        print(f"Error initializing Firebase Admin: {e}")

initialize_firebase()

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# ======================
# Application Routes
# ======================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/auth')
def auth():
    return render_template('auth.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/login', methods=['POST'])
def login():
    token = request.json.get('token')
    
    try:
        decoded_token = firebase_admin.auth.verify_id_token(token)
        uid = decoded_token['uid']
        user = User(uid)
        login_user(user)  
        print(f"Successfully authenticated and logged in user: {uid}")
        return jsonify({
            'success': True,
            'user': {
                'uid': uid,
                'email': decoded_token.get('email')
            }
        })
    except ValueError as e:
        print(f"Invalid token: {e}")  # Debug log
        return jsonify({'success': False, 'error': 'Invalid token'}), 401
    except firebase_admin.exceptions.FirebaseError as e:
        print(f"Firebase error: {e}")  # Debug log
        return jsonify({'success': False, 'error': str(e)}), 401

@app.route('/assessment', methods=['GET','POST'])
@login_required
def assessment():
    if request.method == 'POST':
        form_data = request.form.to_dict()
        # Prepare input for model (mapping form fields to model expected columns)
        model_input = {
            'age': int(request.form['age']),
            'sex': 1 if request.form['sex'] == 'male' else 0,
            'cp': int(request.form['chest_pain']),
            'bps': int(request.form['resting_bp']),
            'chol': int(request.form['cholesterol']),
            'fbs': int(request.form.get('fasting_bs', 0)),
            'restecg': int(request.form['restecg']),
            'mhr': int(request.form['max_hr']),
            'exang': int(request.form.get('exercise_angina', 0)),
            'oldpeak': float(request.form['st_depression']),
            'slope': int(request.form['st_slope']),
            'ca': int(request.form['vessels']),
            'thal': int(request.form['thalassemia'])
        }
        
        # Get prediction using your model
        prediction = predictor.predict_risk(model_input)
        
        # Prepare features for display (using actual feature importance)
        features = {
            feature: importance * 100  # Convert to percentage
            for feature, importance in prediction['feature_importance'].items()
            if feature in model_input  # Only show features we actually collected
        }

        db = firestore.client()

        # Store the data
        if current_user.is_authenticated:
            user_id = current_user.get_id()
            print('user_id : app.py', user_id) # debug code
            user_ref = db.collection('users').document(user_id)
            assessment_ref = user_ref.collection('assessments').document()

            assessment_data = {
                'timestamp': datetime.now(timezone.utc),
                'risk_percent': prediction['probability'],
                'risk_level': prediction['risk_level'],
                'recommendation': prediction['recommendation'],
                **model_input
            }
            print(assessment_data) # debug code
            assessment_ref.set(assessment_data)

        session['show_toast'] = True

        return render_template('results.html',
                                risk_percent=prediction['probability'],
                                risk_level=prediction['risk_level'],
                                color=prediction['color'],
                                features=features)
    return render_template('assessment.html')

@app.route('/results')
@login_required
def results():
    """Assessment results page"""
    if 'assessment_results' not in session:
        return redirect(url_for('assessment'))
    
    risk_percent = request.args.get('risk_percent', 0)
    risk_level = request.args.get('risk_level', 'Medium')
    features = json.loads(request.args.get('features', '{}'))
    
    # Determine alert color based on risk level
    color = "success" if risk_level == "Low" else "warning" if risk_level == "Medium" else "danger"
    show_toast = session.pop('show_toast', False)
    return render_template('results.html',
                         risk_percent=risk_percent,
                         risk_level=risk_level,
                         features=features,
                         color=color,
                         show_toast=show_toast)

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard route"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth'))

    db = firestore.client()
    user_id = current_user.get_id()

    # Get the latest 6 assessments from Firestore
    user_ref = db.collection('users').document(user_id)
    assessments_ref = user_ref.collection('assessments').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(6)
    docs = assessments_ref.stream()

    history = []
    for doc in docs:
        data = doc.to_dict()
        history.append({
            'date': data['timestamp'].strftime('%Y-%m-%d') if 'timestamp' in data else 'Unknown',
            'risk': data.get('risk_percent', 50),
            'level': data.get('risk_level', 'Medium'),
            'details': data
        })

    # If no real data exists, show mock data
    if not history:
        for i in range(3):
            history.append({
                'date': (datetime.now() - timedelta(days=30*(3-i))).strftime('%Y-%m-%d'),
                'risk': max(5, min(95, 30 + i*20)),
                'level': 'Medium',
                'details': {
                    'bps': 120,
                    'chol': 200,
                    'mhr': 150
                }
            })

    current_risk = history[0]['risk']
    current_level = history[0]['level']
    latest = history[0]['details']

    # Prepare health stats from latest entry
    health_stats = [
        {
            'name': 'Blood Pressure',
            'value': latest.get('bps', 120),
            'icon': 'bi-droplet',
            'color': 'primary',
            'trend': 'down',
            'change': 5
        },
        {
            'name': 'Cholesterol',
            'value': latest.get('chol', 200),
            'icon': 'bi-prescription2',
            'color': 'warning',
            'trend': 'down',
            'change': 8
        },
        {
            'name': 'Max HR',
            'value': latest.get('mhr', 150),
            'icon': 'bi-heart-pulse',
            'color': 'danger',
            'trend': 'up',
            'change': 3
        },
        {
            'name': 'BMI',
            'value': 26.4,  # Still static unless you collect height/weight
            'icon': 'bi-speedometer2',
            'color': 'success',
            'trend': 'down',
            'change': 1.2
        }
    ]

    return render_template('dashboard.html',
                           history_dates=[h['date'] for h in history],
                           history_risks=[h['risk'] for h in history],
                           current_risk_percent=current_risk,
                           risk_level=current_level,
                           health_stats=health_stats,
                           labels=[h['date'] for h in history],  # Risk trend labels
                           values=[h['risk'] for h in history])  # Risk trend values


# ======================
# Helper Functions
# ======================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'csv', 'json'}

# ======================
# Application Entry Point
# ======================

if __name__ == '__main__':
    # Run the Flask application
    app.run(debug=True)