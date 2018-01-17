import requests
import sys
import lxml.html

url = 'https://www.espace-citoyens.net/bordeaux/espace-citoyens/'
username = sys.argv[0]
password = sys.argv[1]

s = requests.Session()
r = s.get(url)
assert r.status_code == 200

root = lxml.html.fromstring(r.text)
root.make_links_absolute(url)
assert len(root.forms) >= 1
login_form = root.forms[0]

login_form.fields.update({'username': username, 'password': password})
r1 = s.post(login_form.action, data={k: v for k, v in login_form.fields.items()})
assert r1.status_code == 200

def logout():
    return s.get('https://www.espace-citoyens.net/bordeaux/espace-citoyens/Home/LogOff')

