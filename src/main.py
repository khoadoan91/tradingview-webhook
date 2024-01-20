"""
FastAPI server for gateway
"""
import random
import pandas
from contextlib import asynccontextmanager
import logging
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
import re
from fastapi import FastAPI
from ib_insync import IB, MarketOrder, Stock, StopLimitOrder, util
import nest_asyncio

from models.tv_body import TradingViewRequestBody
from src.blacklist import BLACK_LIST
from src.svc.auto_trade import place_order

load_dotenv()
PnLEntryMatcher = re.compile('stop: (?P<stop>[0-9.]+) limit1: (?P<limit1>[0-9.]+) limit2: (?P<limit2>[0-9.]+)')
# ExitMatcher = re.compile('')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Read server settings
    """
    ib_gateway_host: str = "ibkr-gateway.tv"
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
      clientId = random.randint(1, 100),
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
  
  place_order(body, ibkr)
  return "Ok"


