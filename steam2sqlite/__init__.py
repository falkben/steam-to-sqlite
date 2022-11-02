__version__ = "0.1.0"


# global constants

# limit is 10 req/10 sec so we batch in groups of 5 and then delay by 5 secs
BATCH_SIZE = 5

APPIDS_URL = "https://api.steampowered.com/ISteamApps/GetAppList/v0002/?format=json"
APPID_URL = "https://store.steampowered.com/api/appdetails/?appids={}&l=english"
ACHIEVEMENT_URL = "https://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2/?gameid={}&format=json"


#! do not go over DAILY_API_LIMIT, currently not used
# DAILY_API_LIMIT = 100_000
