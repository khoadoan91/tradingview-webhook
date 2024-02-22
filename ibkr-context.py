from ib_insync import IB, LimitOrder, Stock, MarketOrder

ibkr = IB()
ibkr.connect(host="ibkr-gateway.tv", port=8888, clientId = 1000, readonly = True)

try:
  contract = Stock("SPY", "SMART", currency="USD")
  contract = ibkr.reqContractDetails(contract)[0].contract
  limit1Order = LimitOrder(action="BUY", totalQuantity=4, lmtPrice=470, tif="GTC")
  trade = ibkr.placeOrder(contract, limit1Order)

  ibkr.placeOrder(contract, MarketOrder(action="SELL", totalQuantity=4))
finally:
  ibkr.disconnect()