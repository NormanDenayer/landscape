import twitter
import sys

api_key = sys.argv[0]
api_secret = sys.argv[1]

access_token = sys.argv[2]
access_secret = sys.argv[3]

def get_app_auth_header():
    import requests
    from base64 import b64encode

    url_app_only = 'https://api.twitter.com/oauth2/token'
    request_token = 'https://api.twitter.com/oauth/request_token'

    # auth the application
    bearer_token_cred = b64encode(f'{api_key}:{api_secret}'.encode()).decode()
    resp = requests.post(url_app_only, {'grant_type':'client_credentials'},
                         headers={'Authorization': f'Basic {bearer_token_cred}',
                                  'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'})
    resp.raise_for_status()

    response = resp.json()
    print('access token : ' + response['access_token'])
    return {'Authorization': 'Bearer ' + response['access_token']}


api = twitter.Api(api_key, api_secret, access_token, access_secret)
for status in api.GetHomeTimeline(count=3):
    print(status.text, end='\n\n')
