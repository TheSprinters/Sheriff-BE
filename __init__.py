from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os


# Load the environment variables from .env file
load_dotenv()


# Setup of key Flask object (app)
app = Flask(__name__)

# Configure Flask Port, default to 8587 which is same as Docker setup
app.config['FLASK_PORT'] = int(os.environ.get('FLASK_PORT') or 8325)

# Configure Flask to handle JSON with UTF-8 encoding versus default ASCII
app.config['JSON_AS_ASCII'] = False


# Allowed servers for cross-origin resource sharing (CORS)
cors = CORS(
   app,
   supports_credentials=True,
   origins=[
       'http://localhost:4500',
       'http://127.0.0.1:4500',
       'http://localhost:4599',
       'http://127.0.0.1:4599',
       'http://localhost:4600',
       'http://127.0.0.1:4600',
       'http://localhost:4000',
       'http://127.0.0.1:4000',
       'https://open-coding-society.github.io',
       'https://pages.opencodingsociety.com',
       'https://dsasd.opencodingsociety.com',
       'https://sheriff.opencodingsociety.com',
   ],
   methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)


# Browser settings
SECRET_KEY = os.environ.get('SECRET_KEY') or 'SECRET_KEY'
SESSION_COOKIE_NAME = os.environ.get('SESSION_COOKIE_NAME') or 'sess_python_flask'
JWT_TOKEN_NAME = os.environ.get('JWT_TOKEN_NAME') or 'jwt_sheriff'
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_COOKIE_NAME'] = SESSION_COOKIE_NAME
app.config['JWT_TOKEN_NAME'] = JWT_TOKEN_NAME


# Database settings
dbName = 'user_management'
DB_ENDPOINT = os.environ.get('DB_ENDPOINT') or None
DB_USERNAME = os.environ.get('DB_USERNAME') or None
DB_PASSWORD = os.environ.get('DB_PASSWORD') or None
if DB_ENDPOINT and DB_USERNAME and DB_PASSWORD:
   # Production - Use MySQL
   DB_PORT = '3306'
   dbURI = f'mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_ENDPOINT}:{DB_PORT}/{dbName}'
   backupURI = None
else:
   # Development - Use SQLite
   dbString = 'sqlite:///volumes/'
   dbURI = dbString + dbName + '.db'
   backupURI = dbString + dbName + '_bak.db'
# Set database configuration in Flask app
app.config['SQLALCHEMY_DATABASE_URI'] = dbURI
app.config['SQLALCHEMY_BACKUP_URI'] = backupURI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Claude API settings (for DSA Sheriff chatbot)
app.config['CLAUDE_API_KEY'] = os.environ.get('CLAUDE_API_KEY') or None
