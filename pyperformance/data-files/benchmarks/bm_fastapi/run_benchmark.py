"""
Test the performance of simple HTTP serving with FastAPI.

This benchmark tests FastAPI's request handling, including:
- Path parameter extraction and validation
- Pydantic model serialization
- JSON response encoding

The bench serves a REST API endpoint that returns JSON objects,
simulating a typical web application scenario.

Author: Savannah Ostrowski
"""

import asyncio
import socket
import time

import httpx
import pyperf
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

HOST = "127.0.0.1"

CONCURRENCY = 150

class Item(BaseModel):
    id: int
    name: str
    price: float
    tags: list[str] = []

app = FastAPI()

@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    return {
        "id": item_id,
        "name": "Sample Item",
        "price": 9.99,
        "tags": ["sample", "item", "fastapi"]
    }


async def run_server_and_benchmark(loops):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, 0))
        s.listen(1)
        port = s.getsockname()[1]

    config = uvicorn.Config(app, host=HOST, port=port, log_level="error")
    server = uvicorn.Server(config)
    server_task = asyncio.create_task(server.serve())

    await asyncio.sleep(0.5)

    async with httpx.AsyncClient() as client:
        t0 = time.perf_counter()

        for i in range(loops):
            tasks = [
                client.get(f"http://{HOST}:{port}/items/{i}")
                for _ in range(CONCURRENCY)
            ]
            responses = await asyncio.gather(*tasks)
            for response in responses:
                response.raise_for_status()
                data = response.json()
                assert data["id"] == i
                assert "tags" in data

        elapsed = time.perf_counter() - t0

    server.should_exit = True
    await server_task
    return elapsed

def bench_fastapi(loops):
    return asyncio.run(run_server_and_benchmark(loops))


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of HTTP requests with FastAPI"
    runner.bench_time_func("fastapi_http", bench_fastapi)
