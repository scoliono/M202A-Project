import asyncio
from advertiser import server
from scanner import client


async def main():
    server_task = asyncio.create_task(server())
    client_task = asyncio.create_task(client())
    await server_task
    await client_task


if __name__ == "__main__":
    asyncio.run(main())
