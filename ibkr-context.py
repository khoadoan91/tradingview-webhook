from contextlib import contextmanager
from ib_insync import IB, LimitOrder, Stock, MarketOrder

@contextmanager
def getIbkr():
  ibkr = IB()
  ibkr.connect(host="ibkr-gateway.tv", port=8888, clientId = 1000, readonly = True)
  try:
    yield ibkr
  finally:
    ibkr.disconnect()
