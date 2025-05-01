# app.py - Combined Flask Application
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from datetime import datetime, timezone, timedelta, date
import pandas as pd
import logging
import json
import firebase_admin
from firebase_admin import auth, credentials, firestore
from werkzeug.utils import secure_filename
import os
from utils.model_predictor import predictor
from utils.meal_planner import get_meal_plan
from utils.medication_reminder import (  # Import your medication functions
    allowed_file, extract_text_from_image, 
    extract_text_from_pdf, parse_medication_details,
    create_reminder_schedule
)
from routes.meal import meal_bp
from routes.medication import med_bp

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

# Register blueprints
app.register_blueprint(meal_bp)
app.register_blueprint(med_bp)

ALLOWED_RISK_LEVELS = ['low', 'moderate', 'high']
ALLOWED_DURATIONS = ['daily', 'week']
ALLOWED_PREFERENCES = ['veg', 'non-veg']

def validate_form_input(risk, pref, duration):
    '''Validate user input against allowed values'''
    errors = []
    
    if risk.lower() not in ALLOWED_RISK_LEVELS:
        errors.append(f"Invalid risk level. Allowed values: {', '.join(ALLOWED_RISK_LEVELS)}")
    
    if pref.lower() not in ALLOWED_PREFERENCES:
        errors.append(f"Invalid preference. Allowed values: {', '.join(ALLOWED_PREFERENCES)}")
    
    if duration.lower() not in ALLOWED_DURATIONS:
        errors.append(f"Invalid duration. Allowed values: {', '.join(ALLOWED_DURATIONS)}")
    
    return errors

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

app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
logger = logging.getLogger(__name__)

# meal planner
@app.route('/meal-planner', methods=['GET', 'POST'])
@login_required
def meal_planner_form():
    try:
        if request.method == 'POST':
            risk = request.form.get('risk', '').lower()
            pref = request.form.get('preference', '').lower()
            duration = request.form.get('duration', '').lower()

            errors = validate_form_input(risk, pref, duration)
            if errors:
                for error in errors:
                    flash(error, 'error')
                return redirect(url_for('meal_planner_form'))

            api_duration = 'day' if duration == 'daily' else 'week'
            data, cal = get_meal_plan(risk, pref, time_frame=api_duration)

            if not data:
                flash("No meal plan found for the given criteria", 'warning')
                return redirect(url_for('meal_planner_form'))

            result = {
                "risk": risk,
                "preference": pref,
                "duration": duration,
                "data": data,
                "calories": cal,
                "generated_date": date.today().strftime("%B %d, %Y")
            }

            flash("Meal plan generated successfully!", 'success')
            return render_template('meal_planner/meal_plan.html', result=result)

    except Exception as e:
        logger.error(f"Error generating meal plan: {str(e)}", exc_info=True)
        flash("An unexpected error occurred. Please try again later.", 'error')
        return redirect(url_for('meal_planner_form'))

    return render_template('meal_planner/meal_plan.html', result=None)

# med reminder
@app.route('/med-reminder', methods=['GET'])
@login_required
def med_reminder_home():
    return render_template('med_reminder/upload.html')

@app.route('/med-reminder/upload', methods=['POST'])
@login_required
def med_reminder_upload():
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('med_reminder_home'))
    
    file = request.files['file']
    notes = request.form.get('notes', '')
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('med_reminder_home'))
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            if filename.lower().endswith('.pdf'):
                text = extract_text_from_pdf(filepath)
            else:
                text = extract_text_from_image(filepath)
            
            medications = parse_medication_details(text + "\n" + notes)
            schedule = create_reminder_schedule(medications)
            
            return render_template('med_reminder/schedule.html', 
                                   medications=medications,
                                   schedule=schedule)
            
        except Exception as e:
            logger.error(f"Error processing medication: {str(e)}")
            flash('Error processing your prescription', 'error')
            return redirect(url_for('med_reminder_home'))
    
    flash('Invalid file type', 'error')
    return redirect(url_for('med_reminder_home'))

# ======================
# Application Entry Point
# ======================

if __name__ == '__main__':
    # Run the Flask application
    app.run(debug=True)