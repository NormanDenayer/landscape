__version__ = '0.0.1'

import asyncio
import logging.config
from jinja2 import PackageLoader, Environment
from urllib.parse import urlparse

from aiohttp import web

@web.middleware
async def handle_cors(request, handler):
    resp = await handler(request)
    DEBUG = True

    if hasattr(request, 'referrer'):
        refer = urlparse(request.referrer)
    origin = '*' if not getattr(request, 'referrer', None) or DEBUG is True else f'{refer.scheme}://{refer.netloc}'
    resp.headers["Access-Control-Allow-Origin"] = origin
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Set-Cookie, Authorization"
    resp.headers["Access-Control-Allow-Credentials"] = "true"
    resp.headers["Access-Control-Allow-Methods"] = "POST, GET, PUT, OPTIONS, DELETE, CREATE"
    return resp


def setup_logging():
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': {
            'default': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            '': {
                'handlers': ['default'],
                'level': 'INFO',
                'propagate': True
            },
            'aiohttp': {
                'handlers': ['default'],
                'level': 'INFO',
                'propagate': False
            },
        }
    }
    logging.config.dictConfig(config)


def setup_template(app):
    app['jinja_env'] = Environment(loader=PackageLoader('landscape', 'templates'), enable_async=True)


def setup_routes(app):
    import os.path
    app.router.add_static('/static/',
                          os.path.join(os.path.abspath(os.path.dirname(__file__)), '../static/')
    )

    from landscape.views import index, widgets, register
    app.router.add_get('/', index)
    app.router.add_get('/user/widgets', widgets)
    app.router.add_post('/register', register)

    from landscape.api import api_login, api_logout, api_widget, api_widget_item, api_widgets, empty_body
    app.router.add_post('/api/v01/login', api_login)
    app.router.add_route('OPTIONS', '/api/v01/login', empty_body)
    app.router.add_get('/api/v01/logout', api_logout)
    app.router.add_route('OPTIONS', '/api/v01/logout', empty_body)
    app.router.add_get('/api/v01/user/{user_id}/widget/{widget_id}', api_widget, name='api_widget')
    app.router.add_route('OPTIONS', '/api/v01/user/{user_id}/widget/{widget_id}', empty_body)
    app.router.add_post('/api/v01/user/{user_id}/widget/{widget_id}', api_widget)
    app.router.add_delete('/api/v01/user/{user_id}/widget/{widget_id}', api_widget)
    app.router.add_post('/api/v01/user/{user_id}/widget/{widget_id}/item/{item_id}', api_widget_item)
    app.router.add_route('OPTIONS', '/api/v01/user/{user_id}/widget/{widget_id}/item/{item_id}', empty_body)
    app.router.add_get('/api/v01/user/{user_id}/widgets', api_widgets)
    app.router.add_route('OPTIONS', '/api/v01/user/{user_id}/widgets', empty_body)
    app.router.add_put('/api/v01/user/{user_id}/widgets', api_widgets)
    app.router.add_post('/api/v01/user/{user_id}/widgets', api_widgets)


def setup_database(app):
    from landscape.controller import DatabaseHandler
    app['db'] = DatabaseHandler.create_connection('./app.db')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = web.Application(debug=False, loop=loop, middlewares=[handle_cors, ],)

    setup_logging()
    setup_template(app)
    setup_routes(app)
    setup_database(app)

    from landscape.tasks import running_bg_jobs
    running_bg_jobs(app['db'])

    web.run_app(app, host='0.0.0.0', port=5000)
