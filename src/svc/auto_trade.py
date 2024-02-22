import asyncio
from dataclasses import asdict
import logging
import math
from ib_insync import IB, Contract, Future, MarketOrder, Stock, StopLimitOrder, Ticker, util

from ..models.all import TradingViewAlert

symbolMapping = {
  "ES1!": ["ES", "FUT"]
}
logger = logging.getLogger(__name__)

async def place_order(alert: TradingViewAlert, ibkr: IB) -> None:
  # Extract info
  contract = tv_to_ib(alert.ticker, ibkr)
  orderSize = await calculate_order_size(ibkr, contract)
  orderSize = abs(float(alert.orderContracts)) * orderSize
  if alert.signal.casefold() == "ENTER".casefold():
    # Place order
    trade = ibkr.placeOrder(contract, MarketOrder(action=str.upper(alert.action), totalQuantity=orderSize))
    
    # TODO: Wrap placeOrder function to async/await
    while not trade.orderStatus.status == 'Filled':
      ibkr.waitOnUpdate()
    logger.info(f"Order filled: {trade}")
    limit1Order = StopLimitOrder(action="SELL" if alert.action == "buy" else "BUY", totalQuantity=math.ceil(orderSize / 2), lmtPrice=alert.limit1, stopPrice=alert.stop, tif="GTC")
    limit2Order = StopLimitOrder(action="SELL" if alert.action == "buy" else "BUY", totalQuantity=math.floor(orderSize / 2), lmtPrice=alert.limit2, stopPrice=alert.stop, tif="GTC")
    limit1Trade = ibkr.placeOrder(contract, limit1Order)
    limit2Trade = ibkr.placeOrder(contract, limit2Order)
    logger.info(f"Place 2 exit orders:\n{limit1Trade}\n{limit2Trade}")
    return
  
  if alert.orderComment.startswith('EXIT 1'):
    trades = ibkr.trades()
    filtered_trades = [trade for trade in trades if trade.contract.symbol == alert.ticker]
    logger.info(f"Found open trades for ticker {alert.ticker}: {filtered_trades}")
    if len(filtered_trades) == 0:
      logger.warn("No positions")
    else:
      order = filtered_trades[0].order
      order.auxPrice = next(pos for pos in ibkr.positions() if pos.contract.symbol == alert.ticker).avgCost
      ibkr.placeOrder(contract, order)
      logger.info(f"Update stoploss of the limit2 order to entry price {order.auxPrice}")

def tv_to_ib(symbol: str, ibkr: IB) -> Contract:
  if symbol in symbolMapping:
    if symbolMapping[symbol][1] == "FUT":
      contract = Future(symbolMapping[symbol], currency="USD")
    else:
      contract = Stock(symbolMapping[symbol], "SMART", currency="USD")
  else:
    contract = Stock(symbol, "SMART", currency="USD")
  return ibkr.reqContractDetails(contract)[0].contract
  
async def calculate_order_size(ibkr: IB, symbol: Contract, allowFundPercent: float = 0.1) -> float:
  availFund = next(account for account in ibkr.accountSummary() if account.tag == 'AvailableFunds').value
  ticker = await reqMktOrderSnapshot(ibkr, symbol, waitForField="ask")
  curPrice = ticker.ask
  return math.floor(availFund * allowFundPercent / curPrice)

async def reqMktOrderSnapshot(ibkr: IB, contract: Contract, waitForField: str = "ask", timeoutInSec: float = 10) -> Ticker:
  tickerEvent = asyncio.Event()
  
  def onTickerUpdate(t: Ticker) -> None:
    if not util.isNan(asdict(t)[waitForField]):
      tickerEvent.set()
  
  ticker = ibkr.reqMktData(contract=contract, snapshot=True)
  ticker.updateEvent += onTickerUpdate
  
  await asyncio.wait_for(tickerEvent.wait(), timeout=timeoutInSec)
  return ticker