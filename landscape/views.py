from aiohttp import web

async def index(request):
    return web.Response(status=200, text='Hello World!')


async def widgets(request):
    tmpl = request.app['jinja_env'].get_template('widgets.html')
    page = await tmpl.render_async()
    return web.Response(status=200, text=page, headers={'Content-Type': 'text/html'})


async def register(request):
    form_data = await request.post()
    request.app['db'].create_user(
        username=form_data['username'], password=form_data['password'], email=form_data['email']
    )
    return web.HTTPFound('/login')
