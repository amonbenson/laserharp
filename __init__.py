import logging
from .config import CONFIG


# configure logging
logging.basicConfig(
    level=CONFIG['log_level'],
    format='%(asctime)s %(levelname)s %(pathname)s: %(message)s')
