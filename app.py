from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
load_dotenv()
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'static/uploads'
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")  # for session and flash messages
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# -------- MongoDB Connection --------
client = MongoClient(os.getenv("MONGO_URI"))  # default port
db = client["portfolio_db"]
messages_collection = db["messages"]
projects_collection = db["projects"]
# -------- Home Page --------
@app.route("/")
def index():
    return render_template("index.html")

# -------- Save Contact Message --------
@app.route("/contact", methods=["POST"])
def contact():
    data = {
        "name": request.form.get("name"),
        "email": request.form.get("email"),
        "message": request.form.get("message"),
        "created_at": datetime.utcnow()
    }
    messages_collection.insert_one(data)
    flash("Message sent successfully!", "success")
    return redirect(url_for("index"))

# -------- Admin Login --------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if "admin_logged_in" in session:
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Replace these with your own admin credentials
        if username == os.getenv("ADMIN_USERNAME") and password == os.getenv("ADMIN_PASSWORD"):
            session["admin_logged_in"] = True
            flash("Logged in successfully!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid username or password!", "danger")
            return redirect(url_for("admin_login"))

    return render_template("admin_login.html")

# -------- Admin Dashboard --------
@app.route("/admin")
def admin_dashboard():
    if "admin_logged_in" not in session:
        flash("Please login first!", "danger")
        return redirect(url_for("admin_login"))

    messages = list(messages_collection.find().sort("created_at", -1))
    return render_template("admin.html", messages=messages)

# -------- Admin Logout --------
@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for("admin_login"))
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Admin Add Project ---
@app.route("/admin/projects", methods=["GET", "POST"])
def admin_projects():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        screenshots = []

        for i in range(1, 4):
            file = request.files.get(f"screenshot{i}")
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.utcnow().timestamp()}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                screenshots.append(f"uploads/{filename}")

        projects_collection.insert_one({
            "title": title,
            "description": description,
            "screenshots": screenshots,
            "created_at": datetime.utcnow()
        })
        flash("Project added successfully!", "success")
        return redirect(url_for("admin_projects"))

    projects = list(projects_collection.find().sort("created_at", -1))
    return render_template("admin_projects.html", projects=projects)

# --- Public Projects Page ---
@app.route("/projects")
def projects_page():
    projects = list(projects_collection.find().sort("created_at", -1))
    return render_template("projects.html", projects=projects)
@app.route("/admin/projects/delete/<project_id>", methods=["POST"])
def delete_project(project_id):
    project = db.projects.find_one({"_id": ObjectId(project_id)})
    if project:
        # Delete all screenshots from static/uploads
        for img in project.get("screenshots", []):
            try:
                os.remove(os.path.join("static", img))
            except FileNotFoundError:
                pass
        # Delete project from MongoDB
        db.projects.delete_one({"_id": ObjectId(project_id)})
        flash("Project deleted successfully.", "success")
    else:
        flash("Project not found.", "danger")
    return redirect(url_for("admin_projects"))
if __name__ == "__main__":
    app.run(debug=True)
