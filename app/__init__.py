from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt # Embora já tenhamos werkzeug.security, bcrypt é mais robusto
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
# bcrypt = Bcrypt(app) # Se quiser usar Flask-Bcrypt
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Nome da função da rota de login
login_manager.login_message_category = 'info'
migrate = Migrate(app, db)

# Garante que a pasta de uploads exista
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

from app import routes, models, forms # Importa as rotas, modelos e formulários
