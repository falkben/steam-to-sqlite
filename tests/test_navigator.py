from unittest.mock import patch

import pytest

from steam2sqlite.navigator import NavigatorError, get, make_requests


@patch.object(get, "__defaults__", (100, None))
@pytest.mark.asyncio
async def test_urls():
    urls = [
        "https://www.google.com",
        "https://www.amazon.com",
        "https://www.youtube.com",
    ]
    responses = await make_requests(urls)

    for resp in responses:
        assert not isinstance(resp, NavigatorError)
        resp.raise_for_status()
