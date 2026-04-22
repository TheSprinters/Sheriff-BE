# imports from flask
from flask import redirect, render_template, request, url_for, jsonify, current_app, g
from flask_login import current_user, login_user, logout_user, LoginManager, login_required
from flask.cli import AppGroup
from dotenv import load_dotenv

# import "objects" from "this" project
from __init__ import app, db

# API endpoints — sheriff only
from api.sheriff import sheriff_api
from api.sheriff_chat import sheriff_chat_api
from api.user import user_api
from api.study import study_api
from api.post import post_api
from api.javascript_exec_api import javascript_exec_api
from api.api_ainpc import ainpc_api
from api.python_exec_api import python_exec_api
from api.persona_api import persona_api
from api.microblog_api import microblog_api
from api.gemini_api import gemini_api
from api.classroom_api import classroom_api
from api.student import student_api
from api.analytics import analytics_api
from api.groq_api import groq_api
from api.pfp import pfp_api
from api.section import section_api
from api.data_export_import_api import data_export_import_api
from api.grade_api import grade_api
from api.feedback_api import feedback_api
from hacks.joke import joke_api
from api.admin_api import admin_api
from api.event_api import event_api

# database Initialization functions
from model.sheriff import Sheriff, initSheriffs
from model.event import initEvents

# Setup Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

import os

# Load environment variables
load_dotenv()

# register URIs for api endpoints — sheriff only
app.register_blueprint(sheriff_api)
app.register_blueprint(sheriff_chat_api)
app.register_blueprint(user_api)
app.register_blueprint(study_api)
app.register_blueprint(post_api)
app.register_blueprint(javascript_exec_api)
app.register_blueprint(ainpc_api)
app.register_blueprint(python_exec_api)
app.register_blueprint(persona_api)
app.register_blueprint(microblog_api)
app.register_blueprint(gemini_api)
app.register_blueprint(classroom_api)
app.register_blueprint(student_api)
app.register_blueprint(analytics_api)
app.register_blueprint(groq_api)
app.register_blueprint(pfp_api)
app.register_blueprint(section_api)
app.register_blueprint(data_export_import_api)
app.register_blueprint(grade_api)
app.register_blueprint(feedback_api)
app.register_blueprint(joke_api)
app.register_blueprint(admin_api)
app.register_blueprint(event_api)

# Tell Flask-Login the view function name of your login route
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return Sheriff.query.get(int(user_id))

@app.context_processor
def inject_user():
    return dict(current_user=current_user)


# ── Routes ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/auth')
def auth_status():
    """Check authentication status for sheriff users."""
    try:
        # Import here to avoid circular imports
        from api.sheriff import decode_sheriff_token
        sheriff = decode_sheriff_token()
        return jsonify({
            "authenticated": True,
            "user": sheriff.read()
        })
    except Exception as e:
        return jsonify({
            "authenticated": False,
            "error": str(e)
        }), 401

@app.route('/u2table')
@login_required
def u2table():
    users = Sheriff.query.all()
    return render_template("u2table.html", user_data=users)

@app.route('/admin-signup')
def admin_signup():
    """Admin signup page for creating initial admin user."""
    return render_template("admin_signup.html")

@app.route('/admin-login')
def admin_login():
    """Admin login page."""
    return render_template("admin_login.html")

@app.route('/admin-panel')
def admin_panel():
    """Admin user-management panel (auth enforced client-side via JWT cookie)."""
    return render_template("admin_panel.html")

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# ── CLI seed command ────────────────────────────────────────────────────────

custom_cli = AppGroup('custom', help='Custom commands')

@custom_cli.command('generate_data')
def generate_data():
    initSheriffs()
    initEvents()

app.cli.add_command(custom_cli)

# ── Run ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    host = "0.0.0.0"
    port = app.config['FLASK_PORT']
    print(f"** Server running: http://localhost:{port}")
    app.run(debug=True, host=host, port=port, use_reloader=False)
