from flask import Flask, request, jsonify, render_template
#from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import pytesseract
from PIL import Image
import pdf2image
import re

# Configuration
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_image(image_path):
    return pytesseract.image_to_string(Image.open(image_path))

def extract_text_from_pdf(pdf_path):
    images = pdf2image.convert_from_path(pdf_path)
    text = ""
    for image in images:
        text += pytesseract.image_to_string(image) + "\n"
    return text

def parse_medication_details(text):
    medications = []
    
    patterns = [
        r'(?P<name>[A-Za-z]+)\s*(?P<dosage>\d+mg)\s*(?P<frequency>\d+\s*times\s*(a|per)\s*day)',
        r'(?P<name>[A-Za-z]+)\s*(?P<dosage>\d+mg)\s*(?P<frequency>every\s*\d+\s*hours)',
        r'(?P<name>[A-Za-z]+)\s*(?P<dosage>\d+mg)\s*(?P<frequency>morning\s*and\s*night)'
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            med = match.groupdict()
            medications.append({
                'name': med['name'].capitalize(),
                'dosage': med['dosage'],
                'frequency': med['frequency']
            })
    
    return medications

def create_reminder_schedule(medications):
    schedule = []
    
    for med in medications:
        if 'morning and night' in med['frequency'].lower():
            schedule.append({
                'medication': med['name'],
                'dosage': med['dosage'],
                'times': ['08:00', '20:00']
            })
        elif 'times a day' in med['frequency'].lower() or 'times per day' in med['frequency'].lower():
            num_times = int(med['frequency'].split()[0])
            times = []
            interval = 24 // num_times
            for i in range(num_times):
                hour = 8 + i*interval
                times.append(f"{hour:02d}:00")
            schedule.append({
                'medication': med['name'],
                'dosage': med['dosage'],
                'times': times
            })
    
    return schedule
