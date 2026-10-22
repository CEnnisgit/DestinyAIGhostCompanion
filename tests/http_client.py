"""Run HTTP requests in one event loop without TestClient's portal thread."""
import asyncio

import httpx


def request(app, method, path, **kwargs):
    async def tick():
        # Some restricted runners cannot wake the loop from worker threads.
        while True:
            await asyncio.sleep(0.01)

    async def send():
        heartbeat = asyncio.create_task(tick())
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            try:
                return await client.request(method, path, **kwargs)
            finally:
                heartbeat.cancel()

    return asyncio.run(send())
