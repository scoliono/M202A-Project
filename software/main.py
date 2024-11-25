import asyncio
from advertiser import server
from scanner import client

async def main():
    # Mock data for files and chunks
    pkg = Package("SamplePackage", 1)
    pkg.write_chunk("/src/file1.txt", 0, b"Hello World", version=1)
    pkg.write_chunk("/src/file2.txt", 0, b"Some data", version=1)

    packages = {
        "SamplePackage": pkg
    }

    server_task = asyncio.create_task(server(packages))
    client_task = asyncio.create_task(client(packages))
    await server_task
    await client_task


if __name__ == "__main__":
    asyncio.run(main())
