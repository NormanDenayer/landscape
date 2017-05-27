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

import logging

l = logging.getLogger('aiohttp')
l.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
l.addHandler(handler)

logger = app.logger
TMC_DATE = re.compile(r'(\w+) (\d{1,2}) (\w+) (\d{4})')
MOIS_2_MONTH = ['JANVIER', 'FEVRIER', 'MARS', 'AVRIL', 'MAI', 'JUIN', 'JUILLET', 'AOUT', 'SEPTEMBRE', 'OCTOBRE', 'NOVEMBRE', 'DECEMBRE']
HASH_URL = lambda url: hashlib.sha1(url).hexdigest()


def limit_html_description(text, limit):
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


# todo: generalize the code to merge with refresh_feed()
async def refresh_tf1(widget):
    if widget.content:
        content = json.loads(widget.content)['items']
    else:
        content = []
    known = [i['id'] for i in content]

    async with aiohttp.ClientSession() as session:
        async with session.get(widget.uri) as resp:
            parsed = html.fromstring(await resp.text(errors='ignore'))
            sections = parsed.xpath("//section[contains(@class, 'no_bg')]")
    channel = {
        'title': parsed.xpath('//title')[0].text,
        'description': '',
        'ttl': '60', # todo: should be 1 day
    }
    for s in sections:
        e = s.find_class('text_title')[0]
        date_title = e.text if e.text is not None else e[0].text
        published_date = translate_french_date(f'{date_title} {datetime.date.today().year}')
        for elt in s.find_class('mosaic_link'):
            article_link = elt.get('href')
            title = elt.find_class('text_title')[0].text
            link = 'https://www.tf1.fr' + article_link
            if HASH_URL(link.encode()) in known:
                continue
            logger.debug('adding %s', title)
            i = {
                'id': HASH_URL(link.encode()),
                'description': '',
                'link': link,
                'title': title,
                'picture': None,
                'at': published_date.replace(tzinfo=timezone('Europe/Brussels')).isoformat(),
                'read': False,
            }
            content.append(i)

    if content and content[0]['at'] is not None:
        content = sorted(content, key=itemgetter('at'), reverse=True)
    if not widget.title:
        widget.title = channel['title']
    widget.content = json.dumps({'channel': channel,'items': content})
    db.session.commit()
    logger.debug('widget %r update with %r', widget, content)


async def refresh_feed(widget):
    if widget.content:
        content = json.loads(widget.content)['items']
    else:
        content = []
    known = [i['id'] for i in content]

    # Need to change the user-agent because theverge.com reject specifically the default agent "python-requests".
    async with aiohttp.ClientSession() as session:
        async with session.get(widget.uri, headers={'User-Agent': 'landscape/0.0.1'}) as resp:
            answer = await resp.text(errors='ignore')
            f = feedparser.parse(answer)
            try:
                f.feed.title
            except AttributeError:
                return
    channel = {
        'title': f.feed.title,
        'description': f.feed.get('description', ''),
        'ttl': f.feed.get('ttl', '60'),
    }
    for item in f.entries:
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


async def refresh_widgets():
    logger.info('refreshing feeds')
    futures = []
    with app.app_context():
        widgets = Widget.query.all()
        for widget in widgets:
            logger.info('refreshing %r', widget)
            if widget.type == WidgetType.FEED:
                try:
                    if 'www.tf1.fr' in widget.uri.lower():
                        fut = refresh_tf1(widget)
                    else:
                        fut = refresh_feed(widget)
                except:
                    logger.exception('impossible to refresh %r', widget)
                else:
                    futures.append(fut)
        await asyncio.gather(*futures)


@app.before_first_request
def running_jobs():
    sched = AsyncIOScheduler(timezone=utc)
    sched.add_job(refresh_widgets, 'interval', minutes=1, id='refresh_feed')
    sched.start()
    logger.info('background jobs started')

    import threading
    #  Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
    try:
        threading.Thread(target=asyncio.get_event_loop().run_forever).start()
    except (KeyboardInterrupt, SystemExit):
        pass
