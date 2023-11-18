from fastapi import FastAPI, Request
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/status")
def get_status():
  current_time = datetime.now()
  return { "now": current_time.isoformat() }

@app.post("/alert-hook")
async def post_alert_hook(request: Request, strategy: str | None = None):
  data = await request.body()
  logger.info(f"Alert received. Strategy: {strategy}. Body: {data}")
  return data
