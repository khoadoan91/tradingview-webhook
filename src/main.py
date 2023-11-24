# pylint: disable=redefined-outer-name, unused-argument
"""
FastAPI server for gateway
"""

from contextlib import asynccontextmanager
import logging
from pydantic_settings import BaseSettings
import re
from fastapi import FastAPI
from ib_insync import IB, MarketOrder, Stock, StopLimitOrder, util
import nest_asyncio

from models.tv_body import TradingViewRequestBody
from src.blacklist import BLACK_LIST

PnLEntryMatcher = re.compile('stop: (?P<stop>[0-9.]+) limit1: (?P<limit1>[0-9.]+) limit2: (?P<limit2>[0-9.]+)')
# ExitMatcher = re.compile('')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Read server settings
    """
    # ibkr.kdoan.duckdns.org
    ib_gateway_host: str = "ibkr.tv.svc.cluster.local"

    # TWS uses 7496 (live) and 7497 (paper), while IB gateway uses 4001 (live) and 4002 (paper).
    ib_gateway_port: int = 8888
    timezone: str = "US/Eastern"
    timeformat: str = "%Y-%m-%dT%H%M"

# from pydantic import BaseModel
# from .gateway import IBConnection

nest_asyncio.apply()
ibkr = IB()
settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
  """
  Connect to gateway
  """
  ibkr.connect(
      host = settings.ib_gateway_host,
      port = settings.ib_gateway_port,
      clientId = 1,
      timeout = 15,
      readonly = False)
  yield
  ibkr.disconnect()

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
  """
  Root path
  """
  return {"Hello": "YES"}

@app.get("/stats")
def stats():
  """
  Perform test of the connection
  """
  results = ibkr.client.connectionStats()
  return results

@app.get("/positions")
def positions():
  """
  Get positions
  """
  results = util.df(ibkr.positions())
  if results:
    return results.transpose()
  return results

@app.get("/portfolio")
def portfolio():
  """
  Get portfolio
  """
  results = util.df(ibkr.portfolio())
  if results:
    return results.transpose()
  return results

@app.post("/alert-hook")
def post_alert_hook(body: TradingViewRequestBody):
  """
  Listen to tradingview alert to place orders.
  """
  logger.info(f"Alert received. Body: {body}")
  if body.ticker in BLACK_LIST:
    return "blacklist"
  
  # Extract info
  contract = Stock(body.ticker, 'SMART', 'USD')
  orderSize = float(body.orderContracts)
  match = PnLEntryMatcher.match(body.orderComment)
  if body.orderComment.startswith('ENTER'):
    # Get stoploss and takeprofit
    stop = float(match.group('stop'))
    limit1 = float(match.group('limit1'))
    limit2 = float(match.group('limit2'))

    # Place order
    trade = ibkr.placeOrder(contract, MarketOrder(action=str.upper(body.orderAction), totalQuantity=orderSize))
    while not trade.orderStatus.status == 'Filled':
      ibkr.waitOnUpdate()
    logger.info(f"Order filled: {trade}")
    limit1Order = StopLimitOrder(action="SELL" if body.orderAction == "buy" else "BUY", totalQuantity=(orderSize / 2), lmtPrice=limit1, stopPrice=stop)
    limit2Order = StopLimitOrder(action="SELL" if body.orderAction == "buy" else "BUY", totalQuantity=(orderSize / 2), lmtPrice=limit2, stopPrice=stop)
    limit1Trade = ibkr.placeOrder(contract, limit1Order)
    limit2Trade = ibkr.placeOrder(contract, limit2Order)
    logger.info(f"Place 2 exit orders:\n{limit1Trade}\n{limit2Trade}")
    return "OK"
  
  if body.orderComment.startswith('EXIT 1'):
    open_orders = ibkr.openOrders()
    filtered_orders = [order for order in open_orders if order.contract.symbol == body.ticker]
    logger.info(f"Found open orders for ticker {body.ticker}: {filtered_orders}")
    if len(filtered_orders) == 0:
      logger.info("Position has lossed")
    else:
      filtered_orders[0].auxPrice = next(pos for pos in ibkr.positions() if pos.contract.symbol == body.ticker).avgCost
      ibkr.placeOrder(filtered_orders[0])
      logger.info(f"Update stoploss of the limit2 order to entry price {filtered_orders[0].auxPrice}")
  
  return "Ok"


