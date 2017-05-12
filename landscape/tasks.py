import requests
import json
import time
import hashlib
import datetime
import locale
from pytz import utc
from lxml import html, etree
from operator import itemgetter
from landscape import app, db
from landscape.models import Widget, WidgetType

from apscheduler.schedulers.background import BackgroundScheduler
import feedparser

logger = app.logger


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


def refresh_tf1(widget):
    if widget.content:
        content = json.loads(widget.content)['items']
    else:
        content = []
    known = [i['id'] for i in content]

    resp = requests.get(widget.uri)
    parsed = html.fromstring(resp.text)
    locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
    sections = parsed.xpath("//section[contains(@class, 'no_bg')]")
    channel = {
        'title': parsed.xpath('//title')[0].text,
        'description': '',
        'ttl': '60', # todo: should be 1 day
    }
    for s in sections:
        e = s.find_class('text_title')[0]
        date_title = e.text if e.text is not None else e[0].text
        published_date = datetime.datetime.strptime(f'{date_title} {datetime.date.today().year}', '%A %d %B %Y')
        for elt in s.find_class('mosaic_link'):
            article_link = elt.get('href')
            title = elt.find_class('text_title')[0].text
            link = 'https://www.tf1.fr' + article_link
            if hashlib.sha1(link.encode()).hexdigest() in known:
                continue
            logger.debug('adding %s', title)
            i = {
                'id': hashlib.sha1(link.encode()).hexdigest(),
                'description': '',
                'link': link,
                'title': title,
                'picture': None,
                'at': published_date.strftime('%D %H:%M'),
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


def refresh_feed(widget):
    if widget.content:
        content = json.loads(widget.content)['items']
    else:
        content = []
    known = [i['id'] for i in content]

    resp = requests.get(widget.uri)
    f = feedparser.parse(resp.text)
    channel = {
        'title': f.feed.title,
        'description': f.feed.get('description', ''),
        'ttl': f.feed.get('ttl', '60'),
    }
    for item in f.entries:
        if hashlib.sha1(item.link.encode()).hexdigest() in known:
            continue
        logger.debug(item)
        picture = None
        for link in item.links + item.get('media_content', []):
            if 'image' in link.get('type', 'image'):
                picture = link.get('href', link.get('url', ''))
                break

        i = {
            'id': hashlib.sha1(item.link.encode()).hexdigest(),
            'description': limit_html_description(item.description, 100),
            'link': item.link,
            'title': item.title,
            'picture': picture,
            'at': time.strftime('%D %H:%M', item.published_parsed) if 'published_parsed' in item.keys() else time.strftime('%D %H:%M', item.updated_parsed) if 'updated_parsed' in item.keys() else None,
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


def refresh_widgets():
    logger.info('refreshing feeds')
    with app.app_context():
        widgets = Widget.query.all()
        for widget in widgets:
            logger.info('refreshing %r', widget)
            if widget.type == WidgetType.FEED:
                try:
                    if 'www.tf1.fr' in widget.uri.lower():
                        refresh_tf1(widget)
                    else:
                        refresh_feed(widget)
                except:
                    logger.exception('impossible to refresh %r', widget)


@app.before_first_request
def running_jobs():
    sched = BackgroundScheduler(timezone=utc)
    sched.add_job(refresh_widgets, 'interval', minutes=1, id='refresh_feed')
    sched.start()
    logger.info('background jobs started')
