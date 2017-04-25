import requests
import json
from lxml import html, etree
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
        # else:
        #     if 'content' in item:
        #         for c in item.content:
        #             m = re.search(r'<img.* src="(.+)".+ />', c.value)
        #             if m is not None:
        #                 picture = m.groups()[0]
        #                 break

        i = {
            'description': limit_html_description(item.description, 60),
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
