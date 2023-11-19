from pydantic import BaseModel

class TradingViewRequestBody(BaseModel):
  orderAction: str
  orderContracts: str
  ticker: str
  positionSize: str
  orderComment: str