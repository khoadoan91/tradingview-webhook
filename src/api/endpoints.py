import asyncio
from dataclasses import asdict
import logging
import traceback
from typing import Annotated, Any, Generator

from fastapi import APIRouter, Body, Depends
from sqlmodel import Session
from ib_insync import util

from ..const import SYMBOL_MAPPING
from ..util import getSettingCurrentTime, timing

from ..svc.alert_trade import RequestMapper
from ..svc.ibOrderOperation import IbOrderOperation

from ..db.engine import engine
from ..models.all import TradersPostRequestBody, TradingViewAlert, TradingViewRequestBody
from ..dependencies import ibkr

logger = logging.getLogger(__name__)
router = APIRouter()

def get_db() -> Generator:
    with Session(engine) as session:
        yield session
SessionDep = Annotated[Session, Depends(get_db)]

@router.post("/alert-hook")
@timing
async def post_alert_hook(
  *, session: SessionDep, body: TradingViewRequestBody):
  """
  Listen to tradingview alert to place orders.
  """
  logger.info(f"Alert received. Body: {body}")
  try:
    alert = RequestMapper.requestMapToAlert(body)
    if alert.ticker in SYMBOL_MAPPING:
      await IbOrderOperation.placeLimitStopOrderAsync(ibkr, alert)
  except Exception as e:
    alert = TradingViewAlert(received_at=getSettingCurrentTime(), ticker=body.ticker, signal="error", action=body.orderAction, error=str(e), content=body.model_dump_json())
    traceback.print_exc()
  session.add(alert)
  session.commit()
  return "Ok"

@router.post("/sim-trade")
@timing
def tradeFromAlertAsync(*, session: SessionDep, payload: Any = Body(None)):
  logger.info(f"Alert received. Request: {payload}")
  requestBody = TradersPostRequestBody(**payload)
  try:
    alert = RequestMapper.requestMapToAlert(requestBody)
    trade = asyncio.run(IbOrderOperation.placeMarketOrderFromAlertAsync(ibkr, alert))
    logger.info(f"Trade info: {trade}")
  except Exception as e:
    alert = TradingViewAlert(received_at=getSettingCurrentTime(), ticker=requestBody.ticker, signal="error", action=requestBody.action, error=str(e), content=requestBody.model_dump_json())
    traceback.print_exc()
  session.add(alert)
  session.commit()
  return "ok"

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

@router.get("/balances")
def balances():
  """Get current balance"""
  accounts = ibkr.accountSummary()
  return accounts