import logging
import httpx
from network import client
from collections import deque
from datetime import datetime
import asyncio

logging.basicConfig(level=logging.INFO)

async def fetch(url: str):
    logging.info(f"Fetching {url}")
    try:
        response = await client.get(url)
        response.raise_for_status()
        logging.info(f"Success: {url}")
        return response.text
    except httpx.RequestError as e:
        logging.error(f"Request error: {e}")
        return None
    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP {e.response.status_code}: {url}")

last_requests = deque(maxlen=5)  # track last 5 requests

async def limited_fetch(url: str):
    now = datetime.now()
    if len(last_requests) == last_requests.maxlen:
        delta = now - last_requests[0]
        if delta.total_seconds() < 1.0:  # max 5 req/sec
            await asyncio.sleep(1.0 - delta.total_seconds())
    last_requests.append(datetime.now())
    return await fetch(url)