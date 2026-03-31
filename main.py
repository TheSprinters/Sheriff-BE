# imports from flask
from flask import redirect, render_template, request, url_for, jsonify
from flask.cli import AppGroup
from dotenv import load_dotenv

# import "objects" from "this" project
from __init__ import app, db

# API endpoints — sheriff only
from api.sheriff import sheriff_api
from api.sheriff_chat import sheriff_chat_api

# database Initialization functions
from model.sheriff import Sheriff, initSheriffs

import os

# Load environment variables
load_dotenv()

# register URIs for api endpoints — sheriff only
app.register_blueprint(sheriff_api)
app.register_blueprint(sheriff_chat_api)


# ── Routes ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/sheriff/')
def sheriff_portal():
    return render_template("index.html")

@app.route('/u2table')
def u2table():
    return "u2table page"


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# ── CLI seed command ────────────────────────────────────────────────────────

custom_cli = AppGroup('custom', help='Custom commands')

@custom_cli.command('generate_data')
def generate_data():
    initSheriffs()

app.cli.add_command(custom_cli)

# ── Run ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    host = "0.0.0.0"
    port = app.config['FLASK_PORT']
    print(f"** Server running: http://localhost:{port}")
    app.run(debug=True, host=host, port=port, use_reloader=False)
