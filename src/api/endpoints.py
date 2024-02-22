import logging
import traceback
from typing import Annotated, Generator

from fastapi import APIRouter, Depends
from sqlmodel import Session
from ib_insync import util

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
  except Exception as e:
    alert = TradingViewAlert(received_at=getSettingCurrentTime(), ticker=body.ticker, signal="error", action=body.orderAction, error=str(e), content=body.model_dump_json())
    traceback.print_exc()
  session.add(alert)
  session.commit()
  # if body.ticker in BLACK_LIST:
  #   return "blacklist"
  
  # place_order(body, ibkr)
  return "Ok"

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
  results = util.df(positions).transpose() if len(positions) > 0 else None
  return results

@router.get("/portfolio")
def portfolio():
  """
  Get portfolio
  """
  portfolio = ibkr.portfolio()
  results = util.df(portfolio).transpose() if len(portfolio) > 0 else None
  return results