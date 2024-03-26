from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from pydantic import BaseModel

class TradingViewAlert(SQLModel, table=True):
  __tablename__ = "tradingview_alert"
  
  id: Optional[int] = Field(default=None, primary_key=True)
  fired_at: Optional[datetime] = None
  received_at: datetime = Field(default=datetime.now())
  ticker: str
  signal: Optional[str] = None
  sentiment: Optional[str] = None
  action: str
  quantity: Optional[int] = None
  limit1: Optional[float] = None
  limit2: Optional[float] = None
  stop: Optional[float] = None
  error: Optional[str] = None
  content: str

class TradingViewRequestBody(BaseModel):
  orderAction: str
  orderContracts: str
  ticker: str
  positionSize: str
  orderComment: str
  
class TradersPostRequestBody(BaseModel):
  ticker: str
  action: str
  sentiment: str
  quantity: int
  price: float
  time: datetime