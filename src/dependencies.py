from ib_insync import IB
from hvac import Client
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  """
  Read server settings
  """
  IB_GATEWAY_HOST: str = "ibkr-gateway.tv"
  IB_GATEWAY_PORT: int = 8888
  TIMEZONE: str = "US/Eastern"
  TIME_FORMAT: str = "%Y-%m-%dT%H%M"
  
  VAULT_ROLE_ID: str
  VAULT_SECRET_ID: str
  VAULT_URL: str
  
  model_config = SettingsConfigDict(env_file=".env")
settings = Settings()

client = Client(
  url=settings.VAULT_URL
)

client.auth.approle.login(
  role_id=settings.VAULT_ROLE_ID,
  secret_id=settings.VAULT_SECRET_ID
)

ibkr = IB()
