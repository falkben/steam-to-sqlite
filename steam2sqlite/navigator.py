import asyncio

from httpx import AsyncClient, Response


async def make_requests(items: list[str]) -> list[Response]:
    """List of urls to a list of responses using asyncio"""

    async with AsyncClient() as client:
        responses = await asyncio.gather(
            *[client.get(item) for item in items]  # , return_exceptions=True
        )

    return responses
