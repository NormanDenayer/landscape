import twitter
import sys
import requests
from base64 import b64encode


api_key = sys.argv[0]
api_secret = sys.argv[1]

url_app_only = 'https://api.twitter.com/oauth2/token'
request_token = 'https://api.twitter.com/oauth/request_token'

bearer_token_cred = '::' + b64encode(f'{api_key}:{api_secret}'.encode())
resp = requests.post(url_app_only, {'grant_type':'client_credentials'}, http_basic_auth=bearer_token_cred)
resp.raise_for_status()

response = resp.json()
print('access token : ' + response['access_token'])

