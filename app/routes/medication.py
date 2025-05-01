from flask import Blueprint, request, render_template
from utils.medication_reminder import (
    allowed_file, extract_text_from_image, extract_text_from_pdf,
    parse_medication_details, create_reminder_schedule
)
import os
from werkzeug.utils import secure_filename

med_bp = Blueprint("med", __name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@med_bp.route("/medication-reminder", methods=["GET", "POST"])
def medication_reminder():
    if request.method == "POST":
        file = request.files.get("file")
        notes = request.form.get("notes", "")
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)
            text = extract_text_from_pdf(path) if filename.endswith('.pdf') else extract_text_from_image(path)
            full_text = text + "\n" + notes
            meds = parse_medication_details(full_text)
            schedule = create_reminder_schedule(meds)
            return render_template("med_reminder/schedule.html", medications=meds, schedule=schedule)
        
        return "Invalid file", 400
    return render_template("med_reminder/upload.html")
