import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    OUTPUT_FOLDER = os.path.join(os.getcwd(), 'output')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max-limit 