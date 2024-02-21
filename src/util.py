from datetime import datetime
from functools import wraps
import logging
from time import time

import pytz

from .dependencies import settings

logger = logging.getLogger(__name__)

def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        logger.info('func:%r args:[%r, %r] took: %2.4f sec' % \
          (f.__name__, args, kw, te-ts))
        return result
    return wrap
  
def getSettingCurrentTime() -> datetime:
  return datetime.now(tz=pytz.timezone(settings.TIMEZONE))