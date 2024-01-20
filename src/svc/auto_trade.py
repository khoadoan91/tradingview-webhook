import logging
import math
import re
from ib_insync import IB, Contract, Future, MarketOrder, Stock, StopLimitOrder

from models.tv_body import TradingViewRequestBody

PnLEntryMatcher = re.compile('stop: (?P<stop>[0-9.]+) limit1: (?P<limit1>[0-9.]+) limit2: (?P<limit2>[0-9.]+)')
symbolMapping = {
  "ES1!": ["ES", "FUT"]
}
logger = logging.getLogger(__name__)

def place_order(body: TradingViewRequestBody, ibkr: IB) -> None:
  # Extract info
  contract = tv_to_ib(body.ticker, ibkr)
  orderSize = abs(float(body.orderContracts)) * calculate_order_size(ibkr, contract)
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
    limit1Order = StopLimitOrder(action="SELL" if body.orderAction == "buy" else "BUY", totalQuantity=(orderSize / 2), lmtPrice=limit1, stopPrice=stop, tif="GTC")
    limit2Order = StopLimitOrder(action="SELL" if body.orderAction == "buy" else "BUY", totalQuantity=(orderSize / 2), lmtPrice=limit2, stopPrice=stop, tif="GTC")
    limit1Trade = ibkr.placeOrder(contract, limit1Order)
    limit2Trade = ibkr.placeOrder(contract, limit2Order)
    logger.info(f"Place 2 exit orders:\n{limit1Trade}\n{limit2Trade}")
    return
  
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

def tv_to_ib(symbol: str, ibkr: IB) -> Contract:
  if symbol in symbolMapping:
    if symbolMapping[symbol][1] == "FUT":
      contract = Future(symbolMapping[symbol], currency="USD")
    else:
      contract = Stock(symbolMapping[symbol], "SMART", currency="USD")
  else:
    contract = Stock(symbol, "SMART", currency="USD")
  return ibkr.reqContractDetails(contract)[0].contract
  
def calculate_order_size(ibkr: IB, symbol: Contract, allowFundPercent: float = 0.1) -> float:
  availFund = next(account for account in ibkr.accountSummary() if account.tag == 'AvailableFunds').value
  # ibkr.reqHistoricalData(symbol)
  ticker = ibkr.reqMktData(symbol, snapshot=True)
  curPrice = ticker.marketPrice()
  return math.floor(availFund * allowFundPercent / curPrice)