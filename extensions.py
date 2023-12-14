from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_login import LoginManager
from flask_migrate import Migrate
import os

app = Flask(__name__)
load_dotenv()
db_url = os.getenv("DATABASE_URL")
key = os.getenv("SECRET_KEY")

app.config['SECRET_KEY'] = key
app.config["SQLALCHEMY_DATABASE_URI"] = db_url

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "danger"
