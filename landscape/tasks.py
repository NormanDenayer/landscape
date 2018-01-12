import json
import time
import hashlib
import datetime
import re
import asyncio
import threading
import aiohttp
import feedparser
import peony
from functools import partial
from pytz import timezone
from lxml import html, etree
from operator import itemgetter
from landscape import app, db
from landscape.models import Widget, WidgetType


logger = app.logger
TMC_DATE = re.compile(r'(\w+) (\d{1,2}) (\w+) (\d{4})')
MOIS_2_MONTH = ['JANVIER', 'FEVRIER', 'MARS', 'AVRIL', 'MAI', 'JUIN', 'JUILLET', 'AOUT', 'SEPTEMBRE', 'OCTOBRE', 'NOVEMBRE', 'DECEMBRE']
HASH_URL = lambda url: hashlib.sha1(url).hexdigest()


class ParsingError(Exception): pass


class NoRerun(Exception): pass


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
    try:
        db.session.commit()
    except:
        logger.exception('fail to commit')
        raise NoRerun()
    logger.debug('widget %r update with %r', widget, content)


api_key = app.config['TWITTER']['api_key']
api_secret = app.config['TWITTER']['api_secret']


async def refresh_tweets(widget):
    content = json.loads(widget.content)
    access_token = content['access_token']
    access_secret = content['access_secret']
    if 'items' not in content:
        content['items'] = []

    client = peony.PeonyClient(consumer_key=api_key, consumer_secret=api_secret,
                               access_token=access_token, access_token_secret=access_secret)

    # is an asynchronous context (StreamContext)
    async with client.userstream.user.get(stall_warnings="true", replies="all") as stream:
        # stream is an asynchronous iterator (StreamResponse)
        async for tweet in stream:
            if 'text' not in tweet or 'event' in tweet:
                continue
            content['items'] = [tweet] + content['items'][:49]
            widget.content = json.dumps(content)
            db.session.commit()


async def refresh_widget(widget):
    logger.info('refreshing %r', widget)
    if widget.type == WidgetType.FEED:
        if 'www.tf1.fr' in widget.uri.lower():
            parser = tf1_feed_parser
        else:
            parser = general_feed_parser
        await refresh_feed(widget, parser=parser)

    elif widget.type == WidgetType.TWITTER:
        await refresh_tweets(widget)


async def run_task(ttl, func, loop):
    try:
        await func()
    except NoRerun:
        logger.info('stop refreshing')
        return
    except: pass

    loop.call_later(ttl, run_task, func, ttl, loop)


@app.before_first_request
def running_jobs():
    loop = asyncio.get_event_loop()

    with app.app_context():
        widgets = Widget.query.all()
        for widget in widgets:
            loop.call_soon(run_task(widget.refresh_freq, partial(refresh_widget, widget), loop))

    logger.info('background jobs started')

    #  Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
    try:
        threading.Thread(target=loop.run_forever).start()
    except (KeyboardInterrupt, SystemExit):
        pass
