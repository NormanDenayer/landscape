import json
import time
import hashlib
import datetime
import re
import asyncio
import aiohttp
from pytz import utc, timezone
from lxml import html, etree
from operator import itemgetter
from landscape import app, db
from landscape.models import Widget, WidgetType

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import feedparser


logger = app.logger
TMC_DATE = re.compile(r'(\w+) (\d{1,2}) (\w+) (\d{4})')
MOIS_2_MONTH = ['JANVIER', 'FEVRIER', 'MARS', 'AVRIL', 'MAI', 'JUIN', 'JUILLET', 'AOUT', 'SEPTEMBRE', 'OCTOBRE', 'NOVEMBRE', 'DECEMBRE']
HASH_URL = lambda url: hashlib.sha1(url).hexdigest()


class ParsingError(Exception): pass


class Namespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def get(self, key, *args):
        try:
            return getattr(self, key)
        except AttributeError as e:
            if len(args) != 0:
                return args[0]
            raise KeyError(e)


def limit_html_description(text, limit):
    """
    Truncate "wisely" the text got in params.
    It truncates after the last word making the text longer than the limit.
    (and append '...')
    """
    try:
        node = html.fromstring(text)
    except etree.ParseError:
        return text[:limit]
    text_len = 0
    result = ''
    for subnode in node.iter():
        if subnode.text is not None:
            text_len += len(subnode.text.split(' '))
            result += subnode.text
        if text_len > limit:
            result = ' '.join(result.split(' ')[:limit]) + '...'
            break
    return result


def translate_french_date(date, no_except=True):
    """
    Because alpine docker container doesn't support well the locales, the date string is translated by code.
    If the date is invalid, it may return the current date time, if no_except is True.
    :param date: a date string
    :return: a datetime
    """
    try:
        _, day, mois, year = TMC_DATE.match(date).groups()
    except AttributeError:
        if no_except:
            return datetime.datetime.now()
        else:
            raise
    else:
        return datetime.datetime(year=int(year), month=MOIS_2_MONTH.index(mois.upper().replace('É', 'E')) + 1, day=int(day))


def general_feed_parser(text):
    f = feedparser.parse(text)
    try:
        f.feed.title
    except AttributeError:
        raise ParsingError('invalid title')
    except Exception as e:
        raise ParsingError(e)
    else:
        return f


def tf1_feed_parser(text):
    parsed = html.fromstring(text)
    sections = parsed.xpath("//section[contains(@class, 'no_bg')]")

    result = Namespace(entries=[])
    result.feed = Namespace(title=parsed.xpath('//title')[0].text, description='', ttl='60')

    for s in sections:
        e = s.find_class('text_title')[0]
        date_title = e.text if e.text is not None else e[0].text
        published_date = translate_french_date(f'{date_title} {datetime.date.today().year}')
        for elt in s.find_class('mosaic_link'):
            article_link = elt.get('href')
            result.entries.append(Namespace(
                link='https://www.tf1.fr' + article_link,
                links=[],
                published_parsed=published_date.timetuple(),
                description='',
                title=elt.find_class('text_title')[0].text,
            ))
    return result


async def refresh_feed(widget, *, parser):
    content = json.loads(widget.content)['items'] if widget.content else []
    known = [i['id'] for i in content]

    # Need to change the user-agent because theverge.com reject specifically the default agent "python-requests".
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(widget.uri, headers={'User-Agent': 'landscape/0.0.1'}) as resp:
                answer = await resp.text(errors='ignore')
                try:
                    parsed_answer = parser(answer)
                except ParsingError:
                    return
        except aiohttp.client_exceptions.ServerDisconnectedError as e:
            logger.exception(f'it seems the server disconnected unexpectedly: {widget.uri} - {e}')
            return
    channel = {
        'title': parsed_answer.feed.title,
        'description': parsed_answer.feed.get('description', ''),
        'ttl': parsed_answer.feed.get('ttl', '60'),
    }
    for item in parsed_answer.entries:
        if HASH_URL(item.link.encode()) in known:
            continue
        logger.debug(item)
        picture = None
        for link in item.links + item.get('media_content', []):
            if 'image' in link.get('type', 'image'):
                picture = link.get('href', link.get('url', ''))
                break

        pub_date = item.get('published_parsed', item.get('updated_parsed', None))
        i = {
            'id': HASH_URL(item.link.encode()),
            'description': limit_html_description(item.description, 100),
            'link': item.link,
            'title': item.title,
            'picture': picture,
            'at': pub_date and datetime.datetime.fromtimestamp(time.mktime(pub_date)).replace(tzinfo=timezone('Europe/Brussels')).isoformat(),
            'read': False,
        }
        content.append(i)
    if content and content[0]['at'] is not None:
        content = sorted(content, key=itemgetter('at'), reverse=True)
    content = content[:20]
    if not widget.title:
        widget.title = channel['title']
    widget.content = json.dumps({'channel': channel,'items': content})
    db.session.commit()
    logger.debug('widget %r update with %r', widget, content)


async def refresh_espace_famille(widget):
    url = 'https://www.espace-citoyens.net/bordeaux/espace-citoyens/'
    content = json.loads(widget.content) if widget.content else {}
    async with aiohttp.ClientSession() as s:
        # get the login form
        r = await s.get(url)
        assert r.status == 200
        root = html.fromstring(await r.text())
        root.make_links_absolute(url)
        assert len(root.forms) >= 1
        login_form = root.forms[0]
        login_form.fields.update({'username': content['username'], 'password': content['password']})
        # login
        r1 = await s.post(login_form.action, data={k: v for k, v in login_form.fields.items()})
        assert r1.status == 200
        # fetch info
        items = []
        try:
            root = html.fromstring(await r1.text())
            for bullet in root.find_class('smarties'):
                match = re.match(r'^(\d+)\s+([\w ]+)$', bullet.getparent().text_content().strip())
                if match is None:
                    continue
                count, category = match.groups()
                items.append((count, category))
        except:
            logger.exception('fail at fetching information')
        # logout
        await s.get('https://www.espace-citoyens.net/bordeaux/espace-citoyens/Home/LogOff')
    if not widget.title:
        widget.title = 'Espace Famille Bordeaux'
    content.update({'items': items})
    widget.content = json.dumps(content)
    db.session.commit()
    logger.debug('widget %r update with %r', widget, content)


async def refresh_widgets():
    logger.info('refreshing feeds')
    futures = []
    with app.app_context():
        widgets = Widget.query.all()
        for widget in widgets:
            logger.info('refreshing %r', widget)

            if widget.type == WidgetType.FEED:
                if 'www.tf1.fr' in widget.uri.lower():
                    parser = tf1_feed_parser
                else:
                    parser = general_feed_parser
                fut = refresh_feed(widget, parser=parser)
            else:
                continue
            futures.append(fut)
        await asyncio.gather(*futures)


async def refresh_hourly():
    logger.info('refreshing hourly feeds')
    futures = []
    with app.app_context():
        widgets = Widget.query.all()
        for widget in widgets:
            logger.info('refreshing %r', widget)

            if widget.type == WidgetType.ESPACE_FAMILLE:
                fut = refresh_espace_famille(widget)
            else:
                continue
            futures.append(fut)
        await asyncio.gather(*futures)


#@app.before_first_request
#def running_jobs():
sched = AsyncIOScheduler(timezone=utc)
sched.add_job(refresh_widgets, 'interval', minutes=1, id='refresh_feed')
sched.add_job(refresh_hourly, 'interval', hours=10, id='refresh_hourly')
sched.start()
logger.info('background jobs started')

import threading
try:
    threading.Thread(target=asyncio.get_event_loop().run_forever).start()
except (KeyboardInterrupt, SystemExit):
    pass
