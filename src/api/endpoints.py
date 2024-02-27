from dataclasses import asdict
import logging
import traceback
from typing import Annotated, Generator

from fastapi import APIRouter, Depends
from sqlmodel import Session
from ib_insync import util

from ..svc.auto_trade import place_order, placeOrderFromAlert
from ..const import WHITE_LIST
from ..util import getSettingCurrentTime, timing

from ..svc.alert_trade import request_map_to_alert

from ..db.engine import engine
from ..models.all import TradingViewAlert, TradingViewRequestBody
from ..dependencies import ibkr

logger = logging.getLogger(__name__)
router = APIRouter()

def get_db() -> Generator:
    with Session(engine) as session:
        yield session
SessionDep = Annotated[Session, Depends(get_db)]

@router.post("/alert-hook")
@timing
def post_alert_hook(
  *, session: SessionDep, body: TradingViewRequestBody):
  """
  Listen to tradingview alert to place orders.
  """
  logger.info(f"Alert received. Body: {body}")
  try:
    alert = request_map_to_alert(body)
    if alert.ticker in WHITE_LIST:
      place_order(alert, ibkr)
  except Exception as e:
    alert = TradingViewAlert(received_at=getSettingCurrentTime(), ticker=body.ticker, signal="error", action=body.orderAction, error=str(e), content=body.model_dump_json())
    traceback.print_exc()
  session.add(alert)
  session.commit()
  return "Ok"

@router.post("/sim-trade")
@timing
def trade_from_alert(request: TradingViewRequestBody):
  alert = request_map_to_alert(request)
  logger.info(f"Alert received. Request: {request}")
  if alert.ticker in WHITE_LIST:
    trade = placeOrderFromAlert(alert, ibkr)
    logger.info(f"Submit order: {trade}")
    return trade.orderStatus.status
  return None

@router.get("/stats")
def stats():
  """
  Perform test of the connection
  """
  results = ibkr.client.connectionStats()
  return results


@router.get("/positions")
def positions():
  """
  Get positions
  """
  positions = ibkr.positions()
  results = util.df(positions).to_dict(orient='records') if len(positions) > 0 else []
  return results

@router.get("/portfolio")
def portfolio():
  """
  Get portfolio
  """
  portfolio = ibkr.portfolio()
  results = util.df(portfolio).to_dict(orient='records') if len(portfolio) > 0 else []
  return results

@router.get("/trades")
def trades():
  """
  Get all trades

  Returns:
      list[Trade]: A list of trades
  """
  return [asdict(trade) for trade in ibkr.trades()]