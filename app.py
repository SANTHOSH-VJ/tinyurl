from flask import Flask, request, jsonify, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
import hashlib
import base64
import os

app = Flask(__name__)

# ---------------------------
#   SUPABASE DATABASE URL
# ---------------------------
# Replace [YOUR_PASSWORD] with your actual DB password
DATABASE_URL = "postgresql://postgres:AaBbCc@10@db.dwatbljnrgszrpmqtusp.supabase.co:5432/postgres"

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------------------
#   DATABASE MODEL
# ---------------------------
class URLMapping(db.Model):
    __tablename__ = "url_mapping"

    id = db.Column(db.BigInteger, primary_key=True)
    long_url = db.Column(db.Text, nullable=False)
    short_url = db.Column(db.String(255), unique=True, nullable=False)
    clicks = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())


# Generate short URL hash (fallback)
def generate_short_url(long_url):
    hash_object = hashlib.sha256(long_url.encode())
    short_hash = base64.urlsafe_b64encode(hash_object.digest())[:6].decode()
    return short_hash


# Home page
@app.route('/')
def home():
    return render_template('index.html')


# Create short URL
@app.route('/shorten', methods=['POST'])
def shorten_url():
    long_url = request.form.get('long_url')
    alias = request.form.get('alias')

    if not long_url:
        return jsonify({"success": False, "error": "Please enter a valid URL"}), 400

    # If custom alias provided
    if alias:
        alias = alias.strip().replace(" ", "-")

        existing = URLMapping.query.filter_by(short_url=alias).first()
        if existing:
            return jsonify({"success": False, "error": "Alias already taken"}), 400

        short_url = alias
    else:
        short_url = generate_short_url(long_url)

    # Check if long URL already exists and return existing short
    existing_url = URLMapping.query.filter_by(long_url=long_url).first()
    if existing_url and not alias:
        return jsonify({"success": True, "short_url": f"{request.host_url}{existing_url.short_url}"})

    # Insert new entry
    new_entry = URLMapping(long_url=long_url, short_url=short_url)
    db.session.add(new_entry)
    db.session.commit()

    return jsonify({"success": True, "short_url": f"{request.host_url}{short_url}"})


# Redirect short → original
@app.route('/<short_url>')
def redirect_url(short_url):
    entry = URLMapping.query.filter_by(short_url=short_url).first()

    if entry:
        entry.clicks += 1
        db.session.commit()
        return redirect(entry.long_url)

    return "Error: Short URL not found", 404


# Run locally
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
