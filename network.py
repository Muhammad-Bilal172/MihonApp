import httpx

client = httpx.AsyncClient(
    headers={
        "User-Agent": "MyMihonWebsite/1.0"
    },
    cookies=httpx.Cookies(),
    timeout=15
)