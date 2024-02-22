from datetime import datetime
from functools import wraps
import logging
from timeit import default_timer as timer
from zoneinfo import ZoneInfo
from .dependencies import settings

logger = logging.getLogger(__name__)

def timing(f):
  @wraps(f)
  def wrap(*args, **kw):
    ts = timer()
    result = f(*args, **kw)
    te = timer()
    logger.info(f'func:{f.__name__} took: {te-ts} sec')
    return result
  return wrap

def timingAsync(f):
  @wraps(f)
  async def wrap(*args, **kw):
    ts = timer()
    result = await f(*args, **kw)
    te = timer()
    logger.info(f'func:{f.__name__} took: {te-ts} sec')
    return result
  return wrap

def getSettingCurrentTime() -> datetime:
  return datetime.now(ZoneInfo(settings.TIMEZONE))