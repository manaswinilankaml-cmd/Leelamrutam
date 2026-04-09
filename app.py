import os
import json
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "super_secret_leelamrutam_key"

# ✅ FIXED DATABASE CONFIG (IMPORTANT)
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set! Check Render environment variables.")

# Fix for old postgres:// format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ------------------ MODEL ------------------
class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(250), nullable=False)

# ------------------ USERS ------------------
USERS = {
    "manaswini": "spiritual",
    "harshini": "devotion"
}

# ------------------ AUTH ------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash("Please log in to write or delete stories.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ------------------ ROUTES ------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in USERS and USERS[username] == password:
            session['logged_in'] = True
            session['username'] = username
            flash("Successfully logged in!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials. Try again.", "error")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Successfully logged out.", "success")
    return redirect(url_for('home'))

@app.route("/<section>")
def section_view(section):
    valid_sections = ["shiva", "shakti", "krishna", "our_space"]

    if section not in valid_sections:
        return redirect(url_for('home'))

    stories_data = []
    stories = Story.query.filter_by(section=section).all()

    for s in stories:
        stories_data.append({
            "title": s.title,
            "content": s.content,
            "author": s.author,
            "date": s.date,
            "filename": s.filename,
            "section_id": s.section
        })

    section_title = section.replace("_", " ").title()
    return render_template("section.html", stories=stories_data, section=section_title, section_id=section)

@app.route("/new_story", methods=["GET", "POST"])
@login_required
def new_story():
    if request.method == "POST":
        title = request.form["title"].strip()
        content = request.form["content"].strip()
        section = request.form["section"]

        if not title or not content:
            flash("Title and content cannot be empty", "error")
            return render_template("new_story.html")

        author = session.get('username', 'Unknown')
        date_str = datetime.now().strftime("%B %d, %Y")

        filename_safe = "".join([c for c in title if c.isalnum() or c == ' ']).rstrip().replace(" ", "_")
        filename = f"{filename_safe}.json"

        new_story = Story(
            title=title,
            content=content,
            author=author,
            date=date_str,
            section=section,
            filename=filename
        )

        db.session.add(new_story)
        db.session.commit()

        flash(f"Story '{title}' saved successfully 🌸", "success")
        return redirect(url_for('section_view', section=section))

    return render_template("new_story.html")

@app.route("/story/<section>/<filename>")
def read_story(section, filename):
    story = Story.query.filter_by(section=section, filename=filename).first()

    if not story:
        flash("Story not found", "error")
        return redirect(url_for('home'))

    data = {
        "title": story.title,
        "content": story.content,
        "author": story.author,
        "date": story.date,
        "filename": story.filename
    }

    return render_template("story.html", story=data, section=section)

@app.route("/delete/<section>/<filename>")
@login_required
def delete_story(section, filename):
    story = Story.query.filter_by(section=section, filename=filename).first()

    if story:
        db.session.delete(story)
        db.session.commit()
        flash(f"Story deleted successfully 🌸", "success")
    else:
        flash("Story not found", "error")

    return redirect(url_for('section_view', section=section))

@app.route("/search")
def search():
    query = request.args.get('q', '').lower()
    results = []

    if query:
        search_filter = f"%{query}%"
        stories = Story.query.filter(
            (Story.title.ilike(search_filter)) |
            (Story.content.ilike(search_filter))
        ).all()

        for s in stories:
            results.append({
                "title": s.title,
                "content": s.content,
                "author": s.author,
                "date": s.date,
                "filename": s.filename,
                "section_id": s.section
            })

    return render_template("search.html", results=results, query=query)

# ------------------ INIT DB ------------------
with app.app_context():
    db.create_all()

# ------------------ RUN ------------------
if __name__ == "__main__":
    app.run(debug=True)