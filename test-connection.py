import argparse
import asyncio
import random
from ib_insync import IB, Contract, MarketOrder, Stock, Ticker, util

# TWS uses 7496 (live) and 7497 (paper), while IB gateway uses 4001 (live) and 4002 (paper).
parser = argparse.ArgumentParser(description="Just an example",
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--host", default="ibkr-gateway.tv")
parser.add_argument("-p", "--port", default=8888)
args = parser.parse_args()
config = vars(args)

host = config["host"]
port = config["port"]
ibkr = IB()
ibkr.connect(
    host=host,
    port=port,
    clientId = random.randint(1, 1000),
    readonly = True)

# def onPendingTickers(tickers: set[Ticker]):
#     d = {i: (c.contract.symbol, c.close) for (i, c) in enumerate(tickers)}
#     ibkr.loopUntil(any(util.isNan(val) for val in d.values()), len(tickers), 10)

# ibkr.pendingTickersEvent += onPendingTickers

# ibkr.pendingTickersEvent -= onPendingTickers

async def reqMktDataSnapshot(contract: Contract):
  ticketUpdateEvent = asyncio.Event()
  
  def onTickerUpdate(t: Ticker) -> None:
    ibkr.loopUntil(not util.isNan(t.close), timeout=10)
    if not util.isNan(t.close):
      ticketUpdateEvent.set()
    else:
      raise TimeoutError(f"Timeout while waiting for {t.contract.symbol}")
  
  ticker = ibkr.reqMktData(contract=contract, snapshot=True)
  ticker.updateEvent += onTickerUpdate
  
  await ticketUpdateEvent.wait()
  return ticker

async def test_place_order(placeOrder: bool = False):
  contract=Stock(symbol="MSFT", exchange="SMART", currency="USD")
  print("===================")
  print("my_contracts", contract)
  contract_details = ibkr.reqContractDetails(contract)
  # print("===================")
  # print("contractDetails", contract_details)
  qualify_contracts = ibkr.qualifyContracts(contract_details[0].contract)
  print("===================")
  print("qualify_contracts", qualify_contracts)
  ibkr.reqMarketDataType(3)
  marketDetails = await reqMktDataSnapshot(contract_details[0].contract)
  # marketDetails=ibkr.reqMktData(contract_details[0].contract, snapshot=True)
  # myMarketDetails=ibkr.reqMktData(contract, snapshot=True)
  
  # print("Sleep for 10 sec ...")
  # ibkr.sleep(10)
  print("==========================================================")
  print("marketDetails", marketDetails)
  print("==========================================================")
  # print("myMarketDetails", myMarketDetails)

  if placeOrder:
    trade = ibkr.placeOrder(contract, MarketOrder(action="SELL", totalQuantity=2))
    print("===================")
    print("Order Placed:", trade)
    while not trade.orderStatus.status == 'Filled':
      ibkr.waitOnUpdate()
    print("===================")
    print("Order Status:", trade)

asyncio.run(test_place_order())
results = ibkr.client.connectionStats()
print(f"connectionStats: {results}")

print(ibkr.portfolio())
print("==========================================================")
print(f"Positions: {ibkr.positions()}")

account = next(account for account in ibkr.accountSummary() if account.tag == 'AvailableFunds')
print("==========================================================")
print(f"Available Funds: {account.value}")

ibkr.disconnect()