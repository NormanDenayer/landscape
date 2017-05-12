import requests
import locale
import datetime
from lxml import html

BASE_URL = 'https://www.tf1.fr'
URL = BASE_URL + '/tmc/quotidien-avec-yann-barthes'

resp = requests.get(URL)
parsed = html.fromstring(resp.text)
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

#print('pretty printed')
#print(html.tostring(parsed, pretty_print=True).decode())

sections = parsed.xpath("//section[contains(@class, 'no_bg')]")
for s in sections:
    e = s.find_class('text_title')[0]
    title = e.text if e.text is not None else e[0].text
    published_date = datetime.datetime.strptime(f'{title} {datetime.date.today().year}', '%A %d %B %Y')
    print(published_date)

    for elt in s.find_class('mosaic_link'):
        article_link = elt.get('href')
        title = elt.find_class('text_title')[0].text
        print(f'{title}-{BASE_URL}{article_link}')
