import json
import logging
import time
import hashlib
import datetime
import re
import asyncio
import aiohttp
import secrets
import feedparser
import collections

from pytz import timezone
from lxml import html, etree
from operator import itemgetter

logger = logging.getLogger('landscape.tasks')
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
    except (etree.ParseError, etree.ParserError):
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


async def refresh_feed(widget, *, db, parser):
    title = widget.title
    content = json.loads(widget.content)['items'] if widget.content else []
    known = [i['id'] for i in content]

    # Need to change the user-agent because theverge.com reject specifically the default agent "python-requests".
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(widget.uri, headers={'User-Agent': 'landscape/0.0.1'}) as resp:
                answer = await resp.text(errors='ignore')
                try:
                    parsed_answer = parser(answer)
                    if not title:
                        widget.title = parsed_answer.feed.title
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
            'description': limit_html_description(item.get('description', ''), 100),
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
    widget.content = json.dumps({'channel': channel,'items': content})
    db.update_widget(widget)
    logger.debug('widget %r update with %r', widget, content)


async def refresh_meteo_france(widget, db):
    url = 'http://www.meteofrance.com/previsions-meteo-france'
    content = json.loads(widget.content) if widget.content else {}

    # 1. get the previsions for the coming days
    async with aiohttp.ClientSession() as s:
        r = await s.get(f'{url}/{content["city"].lower()}/{content["zip_code"]}')
        assert r.status == 200

        text = await r.text()
        root = html.fromstring(text)
        match = re.search(r'codeInsee: "(\d+)"', text)
        code_insee = match.groups()[0] if match is not None else None

        previsions = root.find_class('prevision-horaire')
        previsions_details = collections.defaultdict(dict)

        for prev in previsions:
            for i, time_slice in enumerate(prev.findall('li')):
                if time_slice.findtext('div/h3') is None or time_slice.findtext('button/time') is None:
                    continue
                day = time_slice.findtext('div/h3').strip()
                start_slice = time_slice.findtext('button/time').strip()

                summary = time_slice.find_class('day-summary-label')[0].text.strip()
                temperature = time_slice.find_class('day-summary-temperature')[0].text.strip()

                previsions_details[day][start_slice] = (summary, temperature)
        content['previsions'] = previsions_details

    # 2. get the raining risk level
    if code_insee is not None:
        async with aiohttp.ClientSession() as s:
            url = 'http://www.meteofrance.com/mf3-rpc-portlet/rest/pluie/' + str(code_insee)
            r = await s.get(url)
            assert r.status == 200
            response = await r.json()
            content['niveauPluieNext'] = response.get('niveauPluieNext')
            content['rain_risk_levels'] = [{'y': e['niveauPluie'], 'label': e['niveauPluieText']}
                                           for e in response['dataCadran']]

    widget.content = json.dumps(content)
    db.update_widget(widget)
    logger.debug('widget %r update with %r', widget, content)


async def refresh_espace_famille(widget, db):
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
                items.append({
                    'id': secrets.token_hex(32),
                    'description': '',
                    'link': url,
                    'title': f'{count} in {category}',
                    'picture': None,
                    'at': datetime.datetime.now().replace(tzinfo=timezone('Europe/Brussels')).isoformat(),
                    'read': False,
                })
        except:
            logger.exception('fail at fetching information')
        # logout
        await s.get('https://www.espace-citoyens.net/bordeaux/espace-citoyens/Home/LogOff')
    if not widget.title:
        widget.title = 'Espace Famille Bordeaux'
    content.update({'items': items})
    widget.content = json.dumps(content)
    db.update_widget(widget)
    logger.debug('widget %r update with %r', widget, content)


async def refresh_widgets(db):
    try:
        logger.info('refreshing feeds')
        futures = []

        widgets = db.widgets
        for widget in widgets:
            if widget.type == 'FEED':
                if 'www.tf1.fr' in widget.uri.lower():
                    parser = tf1_feed_parser
                else:
                    parser = general_feed_parser
                logger.info(f'refreshing {widget.title}')
                fut = refresh_feed(widget, parser=parser, db=db)
            elif widget.type == 'METEO_FRANCE':
                fut = refresh_meteo_france(widget, db)
            else:
                continue
            futures.append(fut)
        await asyncio.gather(*futures)
    except:
        logger.exception('fail at refreshing feeds')
    await asyncio.sleep(delay=60 * 5) # every 5 minutes
    asyncio.ensure_future(refresh_widgets(db))


async def refresh_hourly(db):
    try:
        logger.info('refreshing hourly feeds')
        futures = []

        widgets = db.widgets
        for widget in widgets:
            if widget.type == 'ESPACE_FAMILLE':
                logger.info(f'refreshing {widget.title}')
                fut = refresh_espace_famille(widget, db)
            else:
                continue
            futures.append(fut)
        await asyncio.gather(*futures)
    except:
        logger.exception('fail at refreshing hourly')
    await asyncio.sleep(delay=60 * 60) # every hour
    asyncio.ensure_future(refresh_hourly(db))


def running_bg_jobs(db):
    asyncio.ensure_future(refresh_widgets(db))
    asyncio.ensure_future(refresh_hourly(db))
    logger.info('background jobs started')
