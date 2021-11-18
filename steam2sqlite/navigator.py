import asyncio

import httpx


async def get_url(client, url):
    resp = await client.get(url)
    await asyncio.sleep(1)
    return resp


async def make_requests(urls: list[str]) -> list[httpx.Response]:
    """List of urls to a list of responses using asyncio"""

    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    async with httpx.AsyncClient(
        headers={"accept": "application/json"}, timeout=10, limits=limits
    ) as client:

        tasks = [get_url(client, url) for url in urls]
        responses = await asyncio.gather(*tasks)

    return responses
