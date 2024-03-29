import asyncio
from dataclasses import asdict
import logging
import math
from ib_insync import *

from ..models.all import TradingViewAlert

symbolMapping = {
  "ES1!": ["ES", "FUT"],
  "MES1!": ["MES", "FUT"],
  "MES1": ["MES", "FUT"]
}
logger = logging.getLogger(__name__)

async def placeOrderFromAlert(alert: TradingViewAlert, ibkr: IB) -> Trade:
  action = str.upper(alert.action)
  contract = tv_to_ib(alert.ticker, ibkr)
  orderSnapshot = await reqMktOrderSnapshot(ibkr, contract)
  lmtPrice = orderSnapshot.ask if action == "BUY" else orderSnapshot.bid
  limitOrder = LimitOrder(action, alert.quantity, lmtPrice, tif="IOC")
  order = ibkr.placeOrder(contract, limitOrder)
  ibkr.waitOnUpdate()
  return order

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
  if "USD" in symbol:
    contract = Crypto(symbol[:-3], "PAXOS", "USD")
  elif symbol in symbolMapping:
    if symbolMapping[symbol][1] == "FUT":
      contract = Future(symbolMapping[symbol], localSymbol=f"{symbolMapping[symbol]}H4", currency="USD", exchange="CME")
    else:
      contract = Stock(symbolMapping[symbol], "SMART", currency="USD")
  else:
    contract = Stock(symbol, "SMART", currency="USD")
  ibkr.qualifyContractsAsync(contract)
  return contract
  
async def calculate_order_size(ibkr: IB, symbol: Contract, allowFundPercent: float = 0.1) -> float:
  accountSummary = ibkr.accountSummaryAsync()
  [accountSummary, marketPrice] = await asyncio.gather(
      ibkr.accountSummaryAsync(),
      reqMktOrderSnapshot(ibkr, symbol, waitForField="ask")
  )
  availFund = next(account for account in accountSummary if account.tag == 'AvailableFunds').value
  curPrice = marketPrice.ask
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