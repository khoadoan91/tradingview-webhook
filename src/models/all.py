from datetime import datetime
from typing import Union
from sqlmodel import SQLModel
from pydantic import BaseModel

class TradingViewAlert(SQLModel):
  received_at: datetime
  ticker: str
  action: str
  trend: Union[str, None] = None
  quantity: Union[int, None] = None
  limit1: Union[float, None] = None
  limit2: Union[float, None] = None
  stop: Union[float, None] = None
  content: str

class TradingViewRequestBody(BaseModel):
  orderAction: str
  orderContracts: str
  ticker: str
  positionSize: str
  orderComment: str