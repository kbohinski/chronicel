import os
DEBUG = False
TESTING = False
CSRF_ENABLED = True
SECRET_KEY = ''
UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/resumes'
MAX_CONTENT_LENGTH = 5 * 1024 * 1024
SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}'.format(
    username='',
    password='',
    hostname='',
    databasename='',
)
SQLALCHEMY_POOL_RECYCLE = 299
SQLALCHEMY_TRACK_MODIFICATIONS = True
