from datetime import datetime
import logging
from typing import Annotated, Generator

from fastapi import APIRouter, Depends
from requests import Session

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
def post_alert_hook(
  *, session: SessionDep, body: TradingViewRequestBody):
  """
  Listen to tradingview alert to place orders.
  """
  logger.info(f"Alert received. Body: {body}")
  now = datetime.now()
  alert = TradingViewAlert(
    received_at=now,
    ticker=body.ticker,
    action=body.orderAction,
    quantity=body.positionSize)
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
  return 'ok'

@router.get("/portfolio")
def portfolio():
  """
  Get portfolio
  """
  return 'ok'