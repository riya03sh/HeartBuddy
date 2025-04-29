from flask import Flask

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this for production

from app import routes

