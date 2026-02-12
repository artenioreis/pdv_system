import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-muito-dificil'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'app/static/img' # Onde os logos e imagens de produtos serão salvos
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # Limite de 16MB para uploads
