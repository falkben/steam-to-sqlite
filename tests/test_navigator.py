import pytest
from steam2sqlite.navigator import make_requests


@pytest.mark.asyncio
async def test_urls():
    urls = [
        "https://www.google.com",
        "https://www.amazon.com",
        "https://www.reddit.com",
    ]
    responses = await make_requests(urls)

    for resp in responses:
        assert resp.raise_for_status() is None
