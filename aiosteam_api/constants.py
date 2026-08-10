API_BASE_URL = "https://api.steampowered.com"
STORE_BASE_URL = "https://store.steampowered.com"
APP_DETAILS_URL = f"{STORE_BASE_URL}/api/appdetails"
APP_SEARCH_URL = f"{STORE_BASE_URL}/search/suggest"

# Steam silently truncates GetPlayerSummaries when more ids than this are sent in one request
STEAM_IDS_PER_REQUEST = 100

DEFAULT_TIMEOUT = 10
DEFAULT_MAX_CONCURRENCY = 8
DEFAULT_RETRIES = 3
