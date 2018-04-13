import os
DEBUG = False
TESTING = False
CSRF_ENABLED = True
SECRET_KEY = 'changeme'
UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/resumes'
MAX_CONTENT_LENGTH = 5 * 1024 * 1024
SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}'.format(
    username='root',
    password='changeme',
    hostname='mysql',
    databasename='chronicel',
)
SQLALCHEMY_POOL_RECYCLE = 299
SQLALCHEMY_TRACK_MODIFICATIONS = True
