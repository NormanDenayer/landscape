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


#api = twitter.Api(api_key, api_secret, access_token, access_secret)
#for status in api.GetHomeTimeline(count=3):
#    print(status.text, end='\n\n')

import asyncio
from peony import PeonyClient
from peony import EventStream, events


class UserStream(EventStream):

    def stream_request(self):
        """
            The stream_request method returns the request
            that will be used by the stream
        """
        print(self.userstream.user.get(stall_warnings="true", replies="all").url)
        return self.userstream.user.get(stall_warnings="true", replies="all")

    # the on_connect event is triggered on connection to an user stream
    # https://dev.twitter.com/streaming/overview/messages-types#friends-lists-friends
    @events.on_connect.handler
    def connection(self, data):
        print("Connected to stream!")

    # the on_follow event is triggered when the user gets a new follower
    # or the user follows someone
    # https://dev.twitter.com/streaming/overview/messages-types#events-event
    @events.on_follow.handler
    def follow(self, data):
        print("You have a new follower @%s" % data.source.screen_name)

    # the on_tweet event is triggered when a tweet seems to be sent on
    # the stream, by default retweets are included
    @events.on_tweet.handler
    def tweet(self, data):
        import pdb
        pdb.set_trace()
        print(data)


#client = PeonyClient(consumer_key=api_key,
#                     consumer_secret=api_secret,
#                     access_token=access_token,
#                     access_token_secret=access_secret)
# client.event_stream(UserStream)

async def track():
    client = PeonyClient(consumer_key=api_key,
                         consumer_secret=api_secret,
                         access_token=access_token,
                         access_token_secret=access_secret)

    #ctx = client.stream.statuses.filter.post(track="@support,@twitter")
    ctx = client.userstream.user.get(stall_warnings="true", replies="all")

    # ctx is an asynchronous context (StreamContext)
    async with ctx as stream:
        # stream is an asynchronous iterator (StreamResponse)
        async for tweet in stream:
            # you can then access items as you would do with a
            # `PeonyResponse` object
            if 'text' not in tweet or 'event' in tweet:
                continue
            user_id = tweet['user']['id']
            #print(tweet)
            username = tweet.user.screen_name

            msg = f"@{username}: {tweet.text}"
            print(msg)

loop = asyncio.get_event_loop()
loop.run_until_complete(track())
