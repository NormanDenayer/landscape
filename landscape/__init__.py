"""
"""

__version__ = '0.0.1'

import os
import logging
from logging.handlers import RotatingFileHandler
from urllib.parse import urlparse

from flask import Flask, request, abort, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_url


app = Flask(__name__, '/static/')
app.config.from_object(os.environ['APP_SETTINGS'])

# configure the database
db = SQLAlchemy(app)

# configure flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# configure logging
#handler = RotatingFileHandler(app.config.get('LOG_PATH', '/var/log/landscape.log'), maxBytes=30 * 1024 * 1024, backupCount=1)
handler = app.config.get('LOG_HANDLER', logging.StreamHandler())
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s : %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG if app.config.get('DEBUG', False) else logging.INFO)
logger = logging.getLogger('werkzeug')
logger.addHandler(handler)
logger.setLevel(logging.INFO)


@app.after_request
def no_cors(response):
    """
    Deactivate CORS.
    Accept all hosts in DEBUG mode. Accept all hosts without credentials otherwise.
    """
    refer = urlparse(request.referrer)
    origin = '*' if not request.referrer or not app.config.get('DEBUG', False) else f'{refer.scheme}://{refer.netloc}'
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Set-Cookie"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, PUT, OPTIONS, DELETE, CREATE"
    return response


@login_manager.unauthorized_handler
def unauthorized_handler():
    """
    Overrides the default handler to avoid redirecting when using the API.
    """
    if '/api/' in request.url:
        return abort(401)
    else:
        return redirect(login_url(login_manager.login_view, request.url))


# time to import routes
import landscape.controller
import landscape.views
import landscape.api
import landscape.tasks
