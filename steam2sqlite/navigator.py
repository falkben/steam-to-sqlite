import asyncio

import httpx


async def get(client: httpx.AsyncClient, url: str, wait_time=2, headers=None):
    try:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
    except (httpx.TimeoutException, httpx.HTTPError):
        if wait_time > 2 ** 6:
            raise
        print(f"Error in response, trying again in: {wait_time}s")
        await asyncio.sleep(wait_time)
        return await get(client, url, wait_time=wait_time ** 2, headers=headers)

    return resp


async def make_requests(urls: list[str]) -> list[httpx.Response]:
    """List of urls to a list of responses using asyncio"""

    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    async with httpx.AsyncClient(
        headers={"accept": "application/json"}, timeout=10, limits=limits
    ) as client:

        tasks = [get(client, url) for url in urls]
        responses = await asyncio.gather(*tasks)

    return responses  # type: ignore
