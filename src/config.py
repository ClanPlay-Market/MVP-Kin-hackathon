import logging

import kin

NETWORK = 'CUSTOM'
HORIZON_URL = 'https://horizon-kik.kininfrastructure.com'
# noinspection SpellCheckingInspection
PUBLIC_KEY = 'YOUR PUBLIC KEY'
# noinspection SpellCheckingInspection
SECRET_KEY = 'YOUR SECRET KEY'
# noinspection SpellCheckingInspection
KIN_ASSET = kin.Asset('KIN', 'GBQ3DQOA7NF52FVV7ES3CR3ZMHUEY4LTHDAQKDTO6S546JCLFPEQGCPK')

# Your database URL
MONGODB_URI = 'mongodb://localhost/kin'

# Default log level of server logs
LOG_LEVEL_DEFAULT = logging.INFO
# Log files path
SERVER_LOG_PATH = 'logs'
# Format of the log messages
LOG_FORMAT = '%(asctime)s %(levelname)s [%(threadName)s] %(module)s.%(funcName)s %(message)s'

TOURNEY_URL = 'http://127.0.0.1/api/v1/tourneys/%s'

TOURNEY_LENGTH = 5 * 60
TOURNEY_PAY_TIMEOUT = 10 * 60

# noinspection SpellCheckingInspection
TEST_USER_PK = 'TEST USER PRIMARY KEY'
# noinspection SpellCheckingInspection
TEST_USER_SK = 'TEST USER SECRET KEY'
