import logging
import os
from datetime import datetime
from pathlib import Path

import pytz

# warnings.filterwarnings('ignore')

BASE_DIR = Path(__file__).resolve().parent.parent

LOGS_DIR = BASE_DIR / 'logs'
TZ = pytz.timezone('US/Eastern')

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

log_fmt = '%(asctime)s:%(message)s'
date_fmt = '%Y-%m-%d %H:%M:%S'

formatter = logging.Formatter(fmt=log_fmt, datefmt=date_fmt)
file_handler = logging.FileHandler(LOGS_DIR / f'{datetime.now().date()}_scan.log')

file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


def customTime(*args):
    utc_dt = pytz.utc.localize(datetime.utcnow())
    converted = utc_dt.astimezone(TZ)
    return converted.timetuple()


logging.Formatter.converter = customTime
