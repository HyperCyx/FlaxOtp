# === TELEGRAM BOT CONFIGURATION ===
TOKEN = "8018522823:AAEF9LBO6W6OlsL__grsUURLgX2PIClws2Q"
CHANNEL_ID = -1002598958220
CHANNEL_LINK = "https://t.me/+CgIjCeBinD5hMDI1"

# === DATABASE CONFIGURATION ===
MONGO_URI = "mongodb+srv://nooblofi0:YO57TmRbkXiGYBCo@noob.gyu06tt.mongodb.net/?retryWrites=true&w=majority"
DB_NAME =  "TellaBot"
COLLECTION_NAME = "numbers"
COUNTRIES_COLLECTION = "countries"
USERS_COLLECTION = "verified_users"

# === ADMIN CONFIGURATION ===
ADMIN_IDS = {1211362365}

# === SMS API CONFIGURATION ===
SMS_API_BASE_URL = "http://51.83.103.80"
SMS_API_ENDPOINT = "/ints/agent/res/data_smscdr.php"
SMS_API_COOKIE = "PHPSESSID=o38eibu9l81kk5iek0l3sq65ke"

# === OTP MONITORING CONFIGURATION ===
OTP_CHECK_INTERVAL = 5  # Check for new OTPs every 5 seconds
OTP_TIMEOUT = 300  # Return number to pool after 5 minutes if no OTP
MORNING_CALL_TIMEOUT = 120  # Morning call timeout: 2 minutes (120 seconds)

# === TIMEZONE CONFIGURATION ===
TIMEZONE_NAME = 'Asia/Riyadh'

# === ALTERNATIVE SMS API CONFIGURATIONS (from test files) ===
# Alternative SMS API 1 (from test_sms.py)
ALT_SMS_API_BASE_URL_1 = "http://51.83.103.80"
ALT_SMS_API_COOKIE_1 = "PHPSESSID=o38eibu9l81kk5iek0l3sq65ke"

# Alternative SMS API 2 (from test_sms_direct.py)
ALT_SMS_API_BASE_URL_2 = "http://51.83.103.80"
ALT_SMS_API_COOKIE_2 = "PHPSESSID=o38eibu9l81kk5iek0l3sq65ke"

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
    '1': 'us',     # USA/Canada (shared)
    '1242': 'bs',  # Bahamas
    '1246': 'bb',  # Barbados
    '1264': 'ai',  # Anguilla
    '1268': 'ag',  # Antigua and Barbuda
    '1284': 'vg',  # British Virgin Islands
    '1340': 'vi',  # US Virgin Islands
    '1441': 'bm',  # Bermuda
    '1473': 'gd',  # Grenada
    '1649': 'tc',  # Turks and Caicos
    '1664': 'ms',  # Montserrat
    '1670': 'mp',  # Northern Mariana Islands
    '1671': 'gu',  # Guam
    '1684': 'as',  # American Samoa
    '1758': 'lc',  # Saint Lucia
    '1767': 'dm',  # Dominica
    '1784': 'vc',  # Saint Vincent and Grenadines
    '1868': 'tt',  # Trinidad and Tobago
    '1869': 'kn',  # Saint Kitts and Nevis
    '1876': 'jm',  # Jamaica
    '20': 'eg',    # Egypt
    '212': 'ma',   # Morocco
    '213': 'dz',   # Algeria
    '216': 'tn',   # Tunisia
    '218': 'ly',   # Libya
    '220': 'gm',   # Gambia
    '221': 'sn',   # Senegal
    '222': 'mr',   # Mauritania
    '223': 'ml',   # Mali
    '224': 'gn',   # Guinea
    '225': 'ci',   # Ivory Coast
    '226': 'bf',   # Burkina Faso
    '227': 'ne',   # Niger
    '228': 'tg',   # Togo
    '229': 'bj',   # Benin
    '230': 'mu',   # Mauritius
    '231': 'lr',   # Liberia
    '232': 'sl',   # Sierra Leone
    '233': 'gh',   # Ghana
    '234': 'ng',   # Nigeria
    '235': 'td',   # Chad
    '236': 'cf',   # Central African Republic
    '237': 'cm',   # Cameroon
    '238': 'cv',   # Cape Verde
    '239': 'st',   # Sao Tome and Principe
    '240': 'gq',   # Equatorial Guinea
    '241': 'ga',   # Gabon
    '242': 'cg',   # Congo
    '243': 'cd',   # DR Congo
    '244': 'ao',   # Angola
    '245': 'gw',   # Guinea-Bissau
    '246': 'io',   # British Indian Ocean Territory
    '247': 'ac',   # Ascension Island
    '248': 'sc',   # Seychelles
    '249': 'sd',   # Sudan
    '250': 'rw',   # Rwanda
    '251': 'et',   # Ethiopia
    '252': 'so',   # Somalia
    '253': 'dj',   # Djibouti
    '254': 'ke',   # Kenya
    '255': 'tz',   # Tanzania
    '256': 'ug',   # Uganda
    '257': 'bi',   # Burundi
    '258': 'mz',   # Mozambique
    '260': 'zm',   # Zambia
    '261': 'mg',   # Madagascar
    '262': 're',   # Reunion/Mayotte
    '263': 'zw',   # Zimbabwe
    '264': 'na',   # Namibia
    '265': 'mw',   # Malawi
    '266': 'ls',   # Lesotho
    '267': 'bw',   # Botswana
    '268': 'sz',   # Swaziland
    '269': 'km',   # Comoros
    '27': 'za',    # South Africa
    '290': 'sh',   # Saint Helena
    '291': 'er',   # Eritrea
    '297': 'aw',   # Aruba
    '298': 'fo',   # Faroe Islands
    '299': 'gl',   # Greenland
    '30': 'gr',    # Greece
    '31': 'nl',    # Netherlands
    '32': 'be',    # Belgium
    '33': 'fr',    # France
    '34': 'es',    # Spain
    '350': 'gi',   # Gibraltar
    '351': 'pt',   # Portugal
    '352': 'lu',   # Luxembourg
    '353': 'ie',   # Ireland
    '354': 'is',   # Iceland
    '355': 'al',   # Albania
    '356': 'mt',   # Malta
    '357': 'cy',   # Cyprus
    '358': 'fi',   # Finland
    '359': 'bg',   # Bulgaria
    '36': 'hu',    # Hungary
    '370': 'lt',   # Lithuania
    '371': 'lv',   # Latvia
    '372': 'ee',   # Estonia
    '373': 'md',   # Moldova
    '374': 'am',   # Armenia
    '375': 'by',   # Belarus
    '376': 'ad',   # Andorra
    '377': 'mc',   # Monaco
    '378': 'sm',   # San Marino
    '379': 'va',   # Vatican City
    '380': 'ua',   # Ukraine
    '381': 'rs',   # Serbia
    '382': 'me',   # Montenegro
    '383': 'xk',   # Kosovo
    '385': 'hr',   # Croatia
    '386': 'si',   # Slovenia
    '387': 'ba',   # Bosnia and Herzegovina
    '389': 'mk',   # North Macedonia
    '39': 'it',    # Italy
    '40': 'ro',    # Romania
    '41': 'ch',    # Switzerland
    '420': 'cz',   # Czech Republic
    '421': 'sk',   # Slovakia
    '423': 'li',   # Liechtenstein
    '43': 'at',    # Austria
    '44': 'gb',    # UK
    '45': 'dk',    # Denmark
    '46': 'se',    # Sweden
    '47': 'no',    # Norway/Svalbard
    '48': 'pl',    # Poland
    '49': 'de',    # Germany
    '51': 'pe',    # Peru
    '52': 'mx',    # Mexico
    '53': 'cu',    # Cuba
    '54': 'ar',    # Argentina
    '55': 'br',    # Brazil
    '56': 'cl',    # Chile
    '57': 'co',    # Colombia
    '58': 've',    # Venezuela
    '591': 'bo',   # Bolivia
    '592': 'gy',   # Guyana
    '593': 'ec',   # Ecuador
    '594': 'gf',   # French Guiana
    '595': 'py',   # Paraguay
    '596': 'mq',   # Martinique
    '597': 'sr',   # Suriname
    '598': 'uy',   # Uruguay
    '599': 'an',   # Netherlands Antilles
    '60': 'my',    # Malaysia
    '61': 'au',    # Australia
    '62': 'id',    # Indonesia
    '63': 'ph',    # Philippines
    '64': 'nz',    # New Zealand
    '65': 'sg',    # Singapore
    '66': 'th',    # Thailand
    '670': 'tl',   # Timor-Leste
    '672': 'aq',   # Antarctica
    '673': 'bn',   # Brunei
    '674': 'nr',   # Nauru
    '675': 'pg',   # Papua New Guinea
    '676': 'to',   # Tonga
    '677': 'sb',   # Solomon Islands
    '678': 'vu',   # Vanuatu
    '679': 'fj',   # Fiji
    '680': 'pw',   # Palau
    '681': 'wf',   # Wallis and Futuna
    '682': 'ck',   # Cook Islands
    '683': 'nu',   # Niue
    '685': 'ws',   # Samoa
    '686': 'ki',   # Kiribati
    '687': 'nc',   # New Caledonia
    '688': 'tv',   # Tuvalu
    '689': 'pf',   # French Polynesia
    '690': 'tk',   # Tokelau
    '691': 'fm',   # Micronesia
    '692': 'mh',   # Marshall Islands
    '7': 'ru',     # Russia/Kazakhstan
    '81': 'jp',    # Japan
    '82': 'kr',    # South Korea
    '84': 'vn',    # Vietnam
    '850': 'kp',   # North Korea
    '852': 'hk',   # Hong Kong
    '853': 'mo',   # Macau
    '855': 'kh',   # Cambodia
    '856': 'la',   # Laos
    '86': 'cn',    # China
    '880': 'bd',   # Bangladesh
    '886': 'tw',   # Taiwan
    '90': 'tr',    # Turkey
    '91': 'in',    # India
    '92': 'pk',    # Pakistan
    '93': 'af',    # Afghanistan
    '94': 'lk',    # Sri Lanka
    '95': 'mm',    # Myanmar
    '960': 'mv',   # Maldives
    '961': 'lb',   # Lebanon
    '962': 'jo',   # Jordan
    '963': 'sy',   # Syria
    '964': 'iq',   # Iraq
    '965': 'kw',   # Kuwait
    '966': 'sa',   # Saudi Arabia
    '967': 'ye',   # Yemen
    '968': 'om',   # Oman
    '970': 'ps',   # Palestine
    '971': 'ae',   # UAE
    '972': 'il',   # Israel
    '973': 'bh',   # Bahrain
    '974': 'qa',   # Qatar
    '975': 'bt',   # Bhutan
    '976': 'mn',   # Mongolia
    '977': 'np',   # Nepal
    '98': 'ir',    # Iran
    '992': 'tj',   # Tajikistan
    '993': 'tm',   # Turkmenistan
    '994': 'az',   # Azerbaijan
    '995': 'ge',   # Georgia
    '996': 'kg',   # Kyrgyzstan
    '998': 'uz',   # Uzbekistan
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