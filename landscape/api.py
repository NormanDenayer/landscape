import json
import logging

from aiohttp import web
from landscape.controller import login_required, Widget

logger = logging.getLogger('aiohttp.access')


async def empty_body(request):
    return web.Response()


async def api_login(request):
    content = await request.json()
    username = content['username']
    password = content['password']
    user = request.app['db'].get_user(username, password)

    if user is None:
        return web.Response(status=401)
    return web.json_response({'token': user.token, 'id': user.user_id})


@login_required
async def api_logout(request, user):
    request.app['db'].reset_user_token(user)
    return web.Response()


@login_required
async def api_widget(request, user):
    """
    Handle RUD operation on a widget.
    (note: for (C)reation see /widgets)
    GET: return detailed info.
    POST: update widget details (title, url).
    DELETE: remove a widget.
    """
    user_id = int(request.match_info['user_id'])
    if user.user_id != user_id:  # ok you are logged but you are not god!
        return web.Response(status=403)

    widget = request.app['db'].get_widget(user_id, request.match_info['widget_id'])
    if widget is None:
        return web.Response(status=404)

    if request.method == 'GET':
        return web.json_response({'widget': widget.as_dict()})

    if request.method == 'POST':  # update an individual widget
        content = await request.json()
        content = content.get('widget')
        if content is None:
            return web.Response()
        widget.title = content.get('title', None) or widget.title
        widget.uri = content.get('uri', None) or widget.uri
        widget_content = content.get('content')
        if widget_content is not None and widget.type == 'LINKS':
            widget.content = json.dumps(widget_content)
        request.app['db'].update_widget(widget)

    if request.method == 'DELETE':
        request.app['db'].delete_widget(widget.widget_id)
    return web.json_response({'widget': widget.as_dict(exclude=['content'])})


@login_required
async def api_widget_item(request, user):
    user_id = int(request.match_info['user_id'])
    if user.user_id != user_id:  # ok you are logged but you are not god!
        return web.Response(status=403)

    widget = request.app['db'].get_widget(user_id, request.match_info['widget_id'])
    if widget is None:
        return web.Response(status=404)

    item_id = request.match_info['item_id']
    content = json.loads(widget.content)
    request_data = await request.json()
    for i in content['items']:
        if i['id'] == item_id:
            i.update({
                'read': request_data.get('read', i.get('read', False)),
            })
            break
    else:
        return web.Response(status=404)
    widget.content = json.dumps(content)
    request.app['db'].update_widget(widget)
    return web.json_response({'widget': widget.as_dict(exclude=['content'])})


@login_required
async def api_widgets(request, user):
    """
    Handle operations on the widgets as collection (aka grid).
    GET: retrieve the list of widgets + position in the grid).
    CREATE: add a widget on the grid.
    POST: update widgets positions.
    """
    user_id = int(request.match_info['user_id'])
    if user.user_id != user_id:  # ok you are logged but you are not god!
        return web.Response(status=403)

    # return the widgets configured (if GET)
    if request.method == 'GET':
        widgets = []
        for w in request.app['db'].get_widgets(user.user_id):
            d = w.as_dict(exclude=['content'])
            d['url'] = str(request.app.router['api_widget'].url_for(user_id=user.user_id, widget_id=w.widget_id))
            widgets.append(d)
        return web.json_response({'widgets': widgets})
    # update the widgets (if PUT)
    content = await request.json()
    if request.method == 'PUT':
        db_widgets = {w.widget_id: w for w in request.app['db'].get_widgets(user_id)}
        for widget in content['widgets']:
            try:
                db_widget = db_widgets[int(widget['i'])]
            except (KeyError, ValueError):
                logger.warning('unknown widget (possible threat): %s for %s', widget['i'], user_id)
                continue
            db_widget.x = widget['x']
            db_widget.y = widget['y']
            db_widget.height = widget['h']
            db_widget.width = widget['w']
            request.app['db'].update_widget(db_widget)
        return web.Response()

    # create a new widget (if POST)
    if request.method == 'POST':
        coord = Widget.new_coordinates(request.app['db'].get_widgets(user_id))
        new_widget = content['widget']
        if new_widget['type'] == 'FEED':
            widget = Widget(
                type='FEED',
                user_id=user_id,
                uri=new_widget['url'],
                title=new_widget['title'],
                refresh_freq=new_widget.get('freq', 60),
                **coord
            )
        elif new_widget['type'] == 'LINKS':
            widget = Widget(
                type='LINKS',
                user_id=user_id,
                uri='',
                title=new_widget['title'],
                refresh_freq=new_widget.get('freq', 60),
                content=json.dumps({
                    'items': new_widget.get('content', {}).get('items', []),
                }),
                **coord
            )
        elif new_widget['type'] == 'ESPACE_FAMILLE':
            widget = Widget(
                type='ESPACE_FAMILLE',
                user_id=user_id,
                uri='',
                title='Espace Famille',
                refresh_freq=new_widget.get('freq', 5*60*60),
                content=json.dumps({
                    'username': new_widget['content'].get('username'),
                    'password': new_widget['content'].get('password'),
                    'items': [],
                }),
                **coord
            )
        elif new_widget['type'] == 'METEO_FRANCE':
            widget = Widget(
                type='METEO_FRANCE',
                user_id=user_id,
                uri='',
                title='Meteo',
                refresh_freq=new_widget.get('freq', 5*60),
                content=json.dumps({
                    'city': new_widget['content'].get('city'),
                    'zip_code': new_widget['content'].get('zip_code'),
                    'previsions': [],
                    'rain_risk_level': [],
                }),
                **coord
            )
        else:
            return web.Response(status=422)

        request.app['db'].add_widget(widget)
        return web.json_response({'widget': widget.as_dict(exclude=['content'])})
