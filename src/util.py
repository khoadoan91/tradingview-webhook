from datetime import datetime
from functools import wraps
import logging
from time import time

from zoneinfo import ZoneInfo
from .dependencies import settings

logger = logging.getLogger(__name__)

def timing(f):
  @wraps(f)
  def wrap(*args, **kw):
    ts = time()
    result = f(*args, **kw)
    te = time()
    logger.info('func:%r took: %2.4f sec' % \
      (f.__name__, args, kw, te-ts))
    return result
  return wrap

def timingAsync(f):
  @wraps(f)
  async def wrap(*args, **kw):
    ts = time()
    result = await f(*args, **kw)
    te = time()
    logger.info('func:%r took: %2.4f sec' % \
      (f.__name__, args, kw, te-ts))
    return result
  return wrap

def getSettingCurrentTime() -> datetime:
  return datetime.now(ZoneInfo(settings.TIMEZONE))