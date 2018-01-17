import requests
import json
import datetime
import lxml.html

url = 'http://www.meteofrance.com/previsions-meteo-france'
city = 'Bordeaux'
zip_code = '33000'

s = requests.Session()
r = s.get(f'{url}/{city.lower()}/{zip_code}')
assert r.status_code == 200
print(f'fetched @ {datetime.datetime.now().replace(microsecond=0).isoformat()}')

root = lxml.html.fromstring(r.text)
previsions = root.find_class('prevision-horaire')

from collections import defaultdict
previsions_details = defaultdict(dict)
for prev in previsions:
    for i, time_slice in enumerate(prev.findall('li')):
        if time_slice.findtext('div/h3') is None or time_slice.findtext('button/time') is None:
            continue
        day = time_slice.findtext('div/h3').strip()
        start_slice = time_slice.findtext('button/time').strip()
        
        summary = time_slice.find_class('day-summary-label')[0].text.strip()
        temperature = time_slice.find_class('day-summary-temperature')[0].text.strip()

        previsions_details[day][start_slice] = (summary, temperature)

s.close()

print(json.dumps(previsions_details, indent=4))
