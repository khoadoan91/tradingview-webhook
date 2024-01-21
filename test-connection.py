import argparse
import random
from ib_insync import IB, MarketOrder, Stock

# TWS uses 7496 (live) and 7497 (paper), while IB gateway uses 4001 (live) and 4002 (paper).
parser = argparse.ArgumentParser(description="Just an example",
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--host", default="127.0.0.1")
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

# def onPendingTickers(tickers):
#     d = {i: (c.contract.symbol, c.close) for (i, c) in enumerate(tickers)}
#     ibkr.loopUntil(any(np.isnan(val) for val in d.values()), len(tickers))

# ibkr.pendingTickersEvent += onPendingTickers

# ibkr.pendingTickersEvent -= onPendingTickers

def test_place_order(placeOrder: bool = False):
  contract=Stock(symbol="MSFT", exchange="SMART", currency="USD")
  print("===================")
  print("my_contracts", contract)
  contract_details = ibkr.reqContractDetails(contract)
  # print("===================")
  # print("contractDetails", contract_details)
  qualify_contracts = ibkr.qualifyContracts(contract_details[0].contract)
  print("===================")
  print("qualify_contracts", qualify_contracts)
  marketDetails=ibkr.reqMktData(contract_details[0].contract, snapshot=True)
  myMarketDetails=ibkr.reqMktData(contract, snapshot=True)
  # while np.isnan(marketDetails.marketPrice()):
  print("Sleep for 10 sec ...")
  ibkr.sleep(10)
  print("==========================================================")
  print("marketDetails", marketDetails.marketPrice())
  print("==========================================================")
  print("myMarketDetails", myMarketDetails)

  if placeOrder:
    trade = ibkr.placeOrder(contract, MarketOrder(action="SELL", totalQuantity=2))
    print("===================")
    print("Order Placed:", trade)
    while not trade.orderStatus.status == 'Filled':
      ibkr.waitOnUpdate()
    print("===================")
    print("Order Status:", trade)

# test_place_order()
results = ibkr.client.connectionStats()
print(f"connectionStats: {results}")

print(ibkr.portfolio())
print("==========================================================")
print(f"Positions: {ibkr.positions()}")

account = next(account for account in ibkr.accountSummary() if account.tag == 'AvailableFunds')
print("==========================================================")
print(f"Available Funds: {account.value}")

ibkr.disconnect()