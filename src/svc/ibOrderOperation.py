
import asyncio
from dataclasses import asdict
import logging
import math
from ib_insync import *

from ..models.all import TradingViewAlert
from ..const import SYMBOL_MAPPING

logger = logging.getLogger(__name__)

class IbOrderOperation:
  @staticmethod
  async def placeOrderFromAlertAsync(ib: IB, alert: TradingViewAlert) -> Trade:
    """
    Place order based on entry and exit
    """
    action = str.upper(alert.action)
    contract = await IbOrderOperation.getIbContractAsync(ib, alert.ticker)
    orderSnapshot = await IbOrderOperation.reqMktOrderSnapshotAsync(ib, contract)
    lmtPrice = orderSnapshot.ask if action == "BUY" else orderSnapshot.bid
    limitOrder = LimitOrder(action, alert.quantity, lmtPrice, tif="IOC")
    order = ib.placeOrder(contract, limitOrder)
    ib.waitOnUpdate()
    return order
  
  @staticmethod
  async def placeMarketOrderFromAlertAsync(ib: IB, alert: TradingViewAlert) -> Trade:
    contract = await IbOrderOperation.getIbContractAsync(ib, alert.ticker)
    order = ib.placeOrder(contract, MarketOrder(str.upper(alert.action), alert.quantity))
    ib.waitOnUpdate()
    return order
  
  @staticmethod
  async def placeLimitStopOrderAsync(alert: TradingViewAlert, ib: IB) -> None:
    """
    Place order based on entry. The alert requires to have limit1, limit2 and stop.
    When limit1 is hit, limit2 order will update the stop to the price that is has entered.
    """
    # Extract info
    contract = await IbOrderOperation.getIbContractAsync(alert.ticker)
    orderSize = alert.quantity
    if alert.signal.casefold() == "ENTER".casefold():
      # Place order
      trade = ib.placeOrder(contract, MarketOrder(action=str.upper(alert.action), totalQuantity=orderSize))
      
      # TODO: Wrap placeOrder function to async/await
      # while not trade.orderStatus.status == 'Filled':
      ib.waitOnUpdate()
      logger.info(f"Order filled: {trade}")
      limit1Order = StopLimitOrder(action="SELL" if alert.action == "buy" else "BUY", totalQuantity=math.ceil(orderSize / 2), lmtPrice=alert.limit1, stopPrice=alert.stop, tif="GTC")
      limit2Order = StopLimitOrder(action="SELL" if alert.action == "buy" else "BUY", totalQuantity=math.floor(orderSize / 2), lmtPrice=alert.limit2, stopPrice=alert.stop, tif="GTC")
      limit1Trade = ib.placeOrder(contract, limit1Order)
      limit2Trade = ib.placeOrder(contract, limit2Order)
      logger.info(f"Place 2 exit orders:\n{limit1Trade}\n{limit2Trade}")
      ib.waitOnUpdate()
      
      return
    
    if alert.orderComment.startswith('EXIT 1'):
      trades = ib.trades()
      filtered_trades = [trade for trade in trades if trade.contract.symbol == alert.ticker]
      logger.info(f"Found open trades for ticker {alert.ticker}: {filtered_trades}")
      if len(filtered_trades) == 0:
        logger.warn("No positions")
      else:
        order = filtered_trades[0].order
        order.auxPrice = next(pos for pos in ib.positions() if pos.contract.symbol == alert.ticker).avgCost
        ib.placeOrder(contract, order)
        logger.info(f"Update stoploss of the limit2 order to entry price {order.auxPrice}")
  
  @staticmethod
  async def reqMktOrderSnapshotAsync(ib: IB, contract: Contract, waitForField: str = "ask", timeoutInSec: float = 10) -> Ticker:
    tickerEvent = asyncio.Event()
    
    def onTickerUpdate(t: Ticker) -> None:
      if not util.isNan(asdict(t)[waitForField]):
        tickerEvent.set()
    
    ticker = ib.reqMktData(contract=contract, snapshot=True)
    ticker.updateEvent += onTickerUpdate
    
    await asyncio.wait_for(tickerEvent.wait(), timeout=timeoutInSec)
    ticker.updateEvent -= onTickerUpdate
    return ticker
  
  @staticmethod
  async def getIbContractAsync(ib: IB, symbol: str) -> Contract:
    if symbol not in SYMBOL_MAPPING:
      raise NameError(f"Unsupported symbol: {symbol}")
    
    mappingInfo = SYMBOL_MAPPING[symbol]
    
    if mappingInfo[1] == Crypto.__name__:
      contract = Crypto(mappingInfo[0], "PAXOS", "USD")
    elif mappingInfo[1] == Future.__name__:
      # TODO: Find a way to get localSymbol
      contract = Future(mappingInfo[0], localSymbol=f"{mappingInfo[0]}H4", exchange="CME", currency="USD")
    elif mappingInfo[1] == Stock.__name__:
      contract = Stock(mappingInfo[0], "SMART", "USD")
    else:
      raise TypeError(f"Unknown contract type: {mappingInfo[1]}")
    
    await ib.qualifyContractsAsync(contract)
    return contract
  
  @staticmethod
  async def calculateOrderSizeAsync(ib: IB, symbol: Contract, allowFundPercent: float = 0.1) -> float:
    accountSummary = ib.accountSummaryAsync()
    [accountSummary, marketPrice] = await asyncio.gather(
        ib.accountSummaryAsync(),
        IbOrderOperation.reqMktOrderSnapshotAsync(ib, symbol, waitForField="ask")
    )
    availFund = next(account for account in accountSummary if account.tag == 'AvailableFunds').value
    curPrice = marketPrice.ask
    return math.floor(availFund * allowFundPercent / curPrice)