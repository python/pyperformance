"""
Benchmark for asyncio TCP server and client performance
transferring 10MB of data.

Author: Kumar Aditya
"""


import asyncio
from pyperf import Runner


CHUNK_SIZE = 1024 ** 2 * 10


async def handle_echo(reader: asyncio.StreamReader,
                      writer: asyncio.StreamWriter) -> None:
    data = b'x' * CHUNK_SIZE
    for _ in range(100):
        writer.write(data)
        await writer.drain()
    writer.close()
    await writer.wait_closed()


async def main() -> None:
    server = await asyncio.start_server(handle_echo, '127.0.0.1', 8882)

    async with server:
        asyncio.create_task(server.start_serving())
        reader, writer = await asyncio.open_connection('127.0.0.1', 8882)
        while True:
            data = await reader.read(CHUNK_SIZE)
            if not data:
                break
        writer.close()
        await writer.wait_closed()

if __name__ == '__main__':
    runner = Runner()
    runner.bench_async_func('asyncio_tcp', main)
