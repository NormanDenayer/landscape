"""
"""

__version__ = '0.0.1'

import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

from logging.handlers import RotatingFileHandler

app = Flask(__name__, '/static/')
app.config.from_object(os.environ['APP_SETTINGS'])

# configure the database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# configure flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# configure logging
handler = RotatingFileHandler(app.config.get('LOG_PATH', '/var/log/landscape.log'), maxBytes=30 * 1024 * 1024, backupCount=1)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s : %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
logger = logging.getLogger('werkzeug')
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

import landscape.controller
import landscape.views
import landscape.tasks
