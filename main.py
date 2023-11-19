from dotenv import load_dotenv
import os
from fastapi import FastAPI
from datetime import datetime
# from ib_insync import *
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import logging

from models.tv_body import TradingViewRequestBody

load_dotenv()

trading_client = TradingClient(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"), paper = True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
# ib = IB()
# ib.connect(host = '192.168.1.123', port = 4002)

@app.get("/status")
def get_status():
  current_time = datetime.now()
  return { "now": current_time.isoformat() }

@app.post("/alert-hook")
async def post_alert_hook(body: TradingViewRequestBody, strategy: str | None = None):
  logger.info(f"Alert received. Body: {body}")

  # preparing order data
  market_order_data = MarketOrderRequest(
                      symbol=body.ticker,
                      qty=float(body.positionSize),
                      side=OrderSide.BUY if body.orderAction == "buy" else OrderSide.SELL,
                      time_in_force=TimeInForce.DAY
                  )
  # Market order
  market_order = trading_client.submit_order(
                  order_data=market_order_data
                  )
  # contract = Stock(body.ticker, 'SMART', 'USD')
  # trade = ib.placeOrder(contract, MarketOrder(action=body.orderAction, totalQuantity=float(body.positionSize)))
  logger.info(market_order)
  return "OK"


