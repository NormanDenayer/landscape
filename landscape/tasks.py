import requests
import json
from itertools import chain
from landscape import app, db
from landscape.models import Widget, WidgetType

from apscheduler.schedulers.background import BackgroundScheduler
import feedparser

logger = app.logger


def refresh_feed(widget):
    resp = requests.get(widget.uri)
    f = feedparser.parse(resp.text)
    channel = {
        'title': f.feed.title,
        'description': f.feed.get('description', ''),
        'ttl': f.feed.get('ttl', '60'),
    }
    content = []
    for item in f.entries:
        logger.info(item)
        picture = None
        for link in item.links + item.get('media_content', []):
            if 'image' in link.get('type', ''):
                picture = link.get('href', link.get('url', ''))
                break

        i = {
            'description': item.description,
            'link': item.link,
            'title': item.title,
            'picture': picture
        }
        content.append(i)
    if not widget.title:
        widget.title = channel['title']
    widget.content = json.dumps({'channel': channel,'items': content})
    db.session.commit()
    logger.info('widget %r update with %r', widget, content)


def refresh_widgets():
    logger.info('refreshing feeds')
    with app.app_context():
        widgets = Widget.query.all()
        for widget in widgets:
            logger.info('refreshing %r', widget)
            if widget.type == WidgetType.FEED:
                try:
                    refresh_feed(widget)
                except:
                    logger.exception('impossible to refresh %r', widget)


@app.before_first_request
def running_jobs():
    sched = BackgroundScheduler()
    sched.add_job(refresh_widgets, 'interval', minutes=1, id='refresh_feed')
    sched.start()
    logger.info('background jobs started')
