"""
FastAPI server for gateway
"""
import random
from contextlib import asynccontextmanager
import logging
from dotenv import load_dotenv
import re
from fastapi import FastAPI

from .dependencies import settings, ibkr
from .api import endpoints
import nest_asyncio
from fastapi.middleware.cors import CORSMiddleware

# from ..blacklist import BLACK_LIST
# from ..svc.auto_trade import place_order

load_dotenv()
PnLEntryMatcher = re.compile('stop: (?P<stop>[0-9.]+) limit1: (?P<limit1>[0-9.]+) limit2: (?P<limit2>[0-9.]+)')
# ExitMatcher = re.compile('')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

nest_asyncio.apply()

@asynccontextmanager
async def lifespan(app: FastAPI):
  """
  Connect to gateway
  """
  ibkr.connect(
      host = settings.IB_GATEWAY_HOST,
      port = settings.IB_GATEWAY_PORT,
      clientId = random.randint(1, 100),
      timeout = 15,
      readonly = False)
  
  # Request Delayed Market Data (FREE - No subscription required)
  ibkr.reqMarketDataType(3)
  yield
  ibkr.disconnect()

app = FastAPI(title="tradingview-webhook"
              , lifespan=lifespan
              )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.tradingview.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router)


