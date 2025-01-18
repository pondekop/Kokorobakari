import os

class Config:
    SQLALCHEMY_DATABASE_URI = f"postgresql://{os.getenv('USER_NAME', 'postgres')}:{os.getenv('USER_PASS', 'postgres')}@pgsql_db:5432/my_database"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_TRACK_MODIFICATIONS = False
