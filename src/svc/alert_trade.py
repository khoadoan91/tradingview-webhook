from datetime import datetime
import re

from ..models.all import TradingViewAlert, TradingViewRequestBody

PnLEntryMatcher = re.compile('stop: (?P<stop>[0-9.]+) limit1: (?P<limit1>[0-9.]+) limit2: (?P<limit2>[0-9.]+)')

def request_map_to_alert(request: TradingViewRequestBody) -> TradingViewAlert:
  if "ENTER" in request.orderComment:
    match = PnLEntryMatcher.match(request.orderComment)
    # Get stoploss and takeprofit
    stop = float(match.group('stop'))
    limit1 = float(match.group('limit1'))
    limit2 = float(match.group('limit2'))
    return TradingViewAlert(
      received_at=datetime.now(),
      ticker=request.ticker,
      action="ENTER",
      trend="UP" if limit2 > limit1 else "DOWN",
      quantity=request.positionSize,
      limit1=limit1,
      limit2=limit2,
      stop=stop,
      content=request.model_dump_json()
    )
  
  return TradingViewAlert(
    received_at=datetime.now(),
    ticker=request.ticker,
    action="EXIT",
    quantity=request.positionSize,
    content=request.model_dump_json()
  )