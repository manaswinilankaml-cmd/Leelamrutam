import os
import json
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, session, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "super_secret_leelamrutam_key"

USERS = {
    "manaswini": "spiritual",
    "harshini": "devotion"
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash("Please log in to write or delete stories.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_story_metadata(section, filename):
    filepath = os.path.join("stories", section, filename)
    if not os.path.exists(filepath):
        return None
    if filename.endswith(".json"):
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                data["filename"] = filename
                return data
            except json.JSONDecodeError:
                return None
    elif filename.endswith(".txt"):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            return {
                "title": filename.replace(".txt", ""),
                "content": content,
                "author": "Legacy Writer",
                "date": "Unknown Date",
                "filename": filename
            }
    return None

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
        
    story_folder = os.path.join("stories", section)
    # create folder if it doesnt exist
    os.makedirs(story_folder, exist_ok=True)
    
    files = os.listdir(story_folder)
    stories_data = []
    for f in files:
        data = get_story_metadata(section, f)
        if data:
            stories_data.append(data)
            
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
        
        filename_safe = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip().replace(" ", "_")
        filename = f"{filename_safe}.json"
        
        filepath = os.path.join("stories", section, filename)
        
        story_data = {
            "title": title,
            "content": content,
            "author": author,
            "date": date_str
        }
        
        os.makedirs(os.path.join("stories", section), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(story_data, file, indent=4)
            
        flash(f"Story '{title}' saved successfully 🌸", "success")
        return redirect(url_for('section_view', section=section))
        
    return render_template("new_story.html")

@app.route("/story/<section>/<filename>")
def read_story(section, filename):
    data = get_story_metadata(section, filename)
    if not data:
        flash("Story not found", "error")
        return redirect(url_for('home'))
        
    return render_template("story.html", story=data, section=section)

@app.route("/delete/<section>/<filename>")
@login_required
def delete_story(section, filename):
    filepath = os.path.join("stories", section, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f"Story deleted successfully 🌸", "success")
    else:
        flash("File not found", "error")
    return redirect(url_for('section_view', section=section))

@app.route("/search")
def search():
    query = request.args.get('q', '').lower()
    results = []
    
    if query:
        sections = ["shiva", "shakti", "krishna", "our_space"]
        for section in sections:
            folder = os.path.join("stories", section)
            if not os.path.exists(folder):
                continue
            for f in os.listdir(folder):
                data = get_story_metadata(section, f)
                if data:
                    if query in data['title'].lower() or query in data['content'].lower():
                        data['section_id'] = section
                        results.append(data)
                        
    return render_template("search.html", results=results, query=query)

if __name__ == "__main__":
    app.run(debug=True)
