"""
"""

__version__ = '0.0.1'

import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from urllib.parse import urlparse
from flask import request

from logging.handlers import RotatingFileHandler

app = Flask(__name__, '/static/')
app.config.from_object(os.environ['APP_SETTINGS'])

# configure the database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# configure flask-login

def unauthorized_handler():
    from flask import request, abort, redirect
    from flask_login.utils import login_url
    if '/api/' in request.url:
        abort(401)
    else:
        return redirect(login_url(login_manager.login_view, request.url))

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.unauthorized_callback = unauthorized_handler

# configure logging
handler = RotatingFileHandler(app.config.get('LOG_PATH', '/var/log/landscape.log'), maxBytes=30 * 1024 * 1024, backupCount=1)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s : %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
logger = logging.getLogger('werkzeug')
logger.addHandler(handler)
logger.setLevel(logging.INFO)


@app.after_request
def no_cors(response):
    origin = '*' if not request.referrer or not app.config.get('DEBUG', False) else '{0.scheme}://{0.netloc}'.format(urlparse(request.referrer))
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Set-Cookie"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, CREATE, OPTIONS"
    return response


import landscape.controller
import landscape.views
import landscape.api
import landscape.tasks
