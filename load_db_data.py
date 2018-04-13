from sqlalchemy_utils import database_exists, create_database
from flask_app import db

print("Attempting to connect to: {}".format(db.get_engine(db.app).url))

if not database_exists(db.get_engine(db.app).url):
    print("Database does not exist. Creating new database.")
    create_database(db.get_engine(db.app).url)

print("Creating chronicel tables.")
db.create_all()
print("Done creating chronicel tables.")

