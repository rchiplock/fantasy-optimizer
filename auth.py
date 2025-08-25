from yahoo_oauth import OAuth2

CONSUMER_KEY = "dj0yJmk9ZkNXYzkwRjI2ekx0JmQ9WVdrOVYwdHNiV0kxZURFbWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PTRk"
CONSUMER_SECRET = "9846985a431e641f2194fe6d74261d2e6f146f20"

try:
    oauth = OAuth2(CONSUMER_KEY, CONSUMER_SECRET, from_file='oauth2.json')
except FileNotFoundError:
    oauth = OAuth2(CONSUMER_KEY, CONSUMER_SECRET)
    # The OAuth2 flow will prompt for authentication and save oauth2.json automatically

if not oauth.token_is_valid():
    oauth.refresh_access_token()

print("Yahoo authentication complete. oauth2.json created!")