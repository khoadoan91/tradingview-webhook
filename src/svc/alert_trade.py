from datetime import datetime
import re

from ..util import getSettingCurrentTime
from ..models.all import TradingViewAlert, TradingViewRequestBody

stopMatcher = re.compile(r'[Ss]top[:]?\s*(?P<stop>[0-9.,]+)')
limit1Matcher = re.compile(r'[Ll]imit\s*1[:]?\s*(?P<limit1>[0-9.,]+)')
limit2Matcher = re.compile(r'[Ll]imit\s*2[:]?\s*(?P<limit1>[0-9.,]+)')

def request_map_to_alert(request: TradingViewRequestBody) -> TradingViewAlert:
  if "ENTER" in request.orderComment:
    # match stoploss
    stopMatch = stopMatcher.search(request.orderComment)
    stop = float(stopMatch.group(1)) if stopMatch is not None else None
    
    # match limit1
    limit1Match = limit1Matcher.search(request.orderComment)
    limit1 = float(limit1Match.group(1)) if limit1Match is not None else None
    
    # match limit2
    limit2Match = limit2Matcher.search(request.orderComment)
    limit2 = float(limit2Match.group(1)) if limit2Match is not None else None
    
    trend = "ERROR" if limit2 is None or limit1 is None else "UP" if limit2 > limit1 else "DOWN"
    
    return TradingViewAlert(
      received_at=getSettingCurrentTime(),
      ticker=request.ticker,
      action="ENTER",
      trend=trend,
      quantity=request.positionSize,
      limit1=limit1,
      limit2=limit2,
      stop=stop,
      content=request.model_dump_json()
    )
  
  return TradingViewAlert(
    received_at=getSettingCurrentTime(),
    ticker=request.ticker,
    action="EXIT",
    quantity=request.positionSize,
    content=request.model_dump_json()
  )