__version__ = "0.1.0"


# global constants

# limit is 10 req/10 sec so we batch in groups of 10 and then delay by 10 seconds
BATCH_SIZE = 10

APPID_URL = "https://store.steampowered.com/api/appdetails/?appids={}"
ACHIEVEMENT_URL = "https://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002/?gameid={}&format=json"


# ! do not go over DAILY_API_LIMIT, curently not used
# DAILY_API_LIMIT = 100_000
