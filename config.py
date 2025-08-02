# === TELEGRAM BOT CONFIGURATION ===
TOKEN = "7650570527:AAG9K_XGEZ2MGcXkBc2h7cltVPQTWayhh00"
CHANNEL_ID = -1002555911826
CHANNEL_LINK = "https://t.me/+6Cw11PRcrFc1NmI1"

# === DATABASE CONFIGURATION ===
MONGO_URI = "mongodb+srv://noob:K3a4ofLngiMG8Hl9@tele.fjm9acq.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "TelegramBotDB"
COLLECTION_NAME = "numbers"
COUNTRIES_COLLECTION = "countries"
USERS_COLLECTION = "verified_users"

# === ADMIN CONFIGURATION ===
ADMIN_IDS = {7762548831, 1211362365}

# === SMS API CONFIGURATION ===
SMS_API_BASE_URL = "http://51.83.103.80"
SMS_API_ENDPOINT = "/ints/agent/res/data_smscdr.php"
SMS_API_COOKIE = "PHPSESSID=jfi9fn51crfub5jj850qte6tah"

# === OTP MONITORING CONFIGURATION ===
OTP_CHECK_INTERVAL = 5  # Check for new OTPs every 5 seconds
OTP_TIMEOUT = 300  # Return number to pool after 5 minutes if no OTP
MORNING_CALL_TIMEOUT = 120  # Morning call timeout: 2 minutes (120 seconds)

# === TIMEZONE CONFIGURATION ===
TIMEZONE_NAME = 'Asia/Riyadh'

# === ALTERNATIVE SMS API CONFIGURATIONS (from test files) ===
# Alternative SMS API 1 (from test_sms.py)
ALT_SMS_API_BASE_URL_1 = "http://54.37.252.85"
ALT_SMS_API_COOKIE_1 = "PHPSESSID=pq0oq4ckbcjnm7dbp6rna1dfdo"

# Alternative SMS API 2 (from test_sms_direct.py)
ALT_SMS_API_BASE_URL_2 = "http://51.83.103.80"
ALT_SMS_API_COOKIE_2 = "PHPSESSID=dn1es46hla171cs6vunle9tq5v"

# === API HEADERS CONFIGURATION ===
SMS_API_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'X-Requested-With': 'XMLHttpRequest',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,ks-IN;q=0.8,ks;q=0.7'
}

# === COUNTRY CODE MAPPING ===
COUNTRY_PREFIXES = {
    '591': 'bo',  # Bolivia
    '51': 'pe',   # Peru
    '1': 'us',    # USA
    '44': 'gb',   # UK
    '91': 'in',   # India
    '966': 'sa',  # Saudi Arabia
    '94': 'lk',   # Sri Lanka
}

# === OTP EXTRACTION PATTERNS ===
OTP_PATTERNS = [
    r'\b(\d{4,6})\b',  # 4-6 digit OTP
    r'code[:\s]*(\d{4,6})',  # "code: 123456"
    r'verification[:\s]*(\d{4,6})',  # "verification: 123456"
    r'OTP[:\s]*(\d{4,6})',  # "OTP: 123456"
    r'password[:\s]*(\d{4,6})',  # "password: 123456"
    r'pin[:\s]*(\d{4,6})',  # "pin: 123456"
    r'passcode[:\s]*(\d{4,6})',  # "passcode: 123456"
    r'(\d{4,6})[^\d]*$',  # OTP at end of message
    r'(\d{4,6})\s+is\s+your',  # "123456 is your"
    r'your\s+(\d{4,6})',  # "your 123456"
]

# === SMS API PARAMETERS TEMPLATE ===
SMS_API_PARAMS_TEMPLATE = {
    'frange': '',
    'fclient': '',
    'fcli': '',
    'fgdate': '',
    'fgmonth': '',
    'fgrange': '',
    'fgclient': '',
    'fgnumber': '',
    'fgcli': '',
    'fg': '0',
    'sEcho': '1',
    'iColumns': '9',
    'sColumns': ',,,,,,,,',
    'iDisplayStart': '0',
    'iDisplayLength': '50',
    'mDataProp_0': '0',
    'sSearch_0': '',
    'bRegex_0': 'false',
    'bSearchable_0': 'true',
    'bSortable_0': 'true',
    'mDataProp_1': '1',
    'sSearch_1': '',
    'bRegex_1': 'false',
    'bSearchable_1': 'true',
    'bSortable_1': 'true',
    'mDataProp_2': '2',
    'sSearch_2': '',
    'bRegex_2': 'false',
    'bSearchable_2': 'true',
    'bSortable_2': 'true',
    'mDataProp_3': '3',
    'sSearch_3': '',
    'bRegex_3': 'false',
    'bSearchable_3': 'true',
    'bSortable_3': 'true',
    'mDataProp_4': '4',
    'sSearch_4': '',
    'bRegex_4': 'false',
    'bSearchable_4': 'true',
    'bSortable_4': 'true',
    'mDataProp_5': '5',
    'sSearch_5': '',
    'bRegex_5': 'false',
    'bSearchable_5': 'true',
    'bSortable_5': 'true',
    'mDataProp_6': '6',
    'sSearch_6': '',
    'bRegex_6': 'false',
    'bSearchable_6': 'true',
    'bSortable_6': 'true',
    'mDataProp_7': '7',
    'sSearch_7': '',
    'bRegex_7': 'false',
    'bSearchable_7': 'true',
    'bSortable_7': 'true',
    'mDataProp_8': '8',
    'sSearch_8': '',
    'bRegex_8': 'false',
    'bSearchable_8': 'true',
    'bSortable_8': 'false',
    'sSearch': '',
    'bRegex': 'false',
    'iSortCol_0': '0',
    'sSortDir_0': 'desc',
    'iSortingCols': '1'
}

# === FILE PATHS ===
USER_CACHE_DIR = "user_cache"

# === LOGGING CONFIGURATION ===
LOGGING_LEVEL = "INFO"