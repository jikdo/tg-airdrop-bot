# import json
# import tweepy

# # get config
# with open(r'config.json', 'r') as file:
#     config = json.loads(file.read())

# auth = tweepy.OAuthHandler(
#     config['access_codes']['twitter_consumer_key'],
#     config['access_codes']['tw_consumer_secret'])

# tw_api = tweepy.API(auth)

# tw_followers = tw_api.tw_followers_ids('pinktaxiglobal')


# def validate_twitter(twitter_username):
#     if twitter_username in tw_followers:
#         return True
