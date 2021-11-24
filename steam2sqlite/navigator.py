import asyncio
import ssl

import httpx
from loguru import logger


class NavigatorError(Exception):
    """Exception for navigator errors (after multiple retries)"""

    def __init__(self, url: str) -> None:
        self.url = url


async def get(
    client: httpx.AsyncClient,
    url: str,
    wait_time: float = 2,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    try:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
    except (httpx.HTTPError, ssl.SSLError) as e:
        if wait_time > 2 ** 6:
            logger.exception(f"Response never succeeded on url {url}")
            raise NavigatorError(url=url) from e
        logger.error(f"Error in response, trying again in: {wait_time}s")
        await asyncio.sleep(wait_time)
        return await get(client, url, wait_time=wait_time * 2, headers=headers)

    return resp


async def make_requests(urls: list[str]) -> list[httpx.Response]:
    """List of urls to a list of responses using asyncio"""

    limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)
    async with httpx.AsyncClient(
        headers={"accept": "application/json"}, timeout=10, limits=limits
    ) as client:

        tasks = [get(client, url) for url in urls]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    return responses  # type: ignore
