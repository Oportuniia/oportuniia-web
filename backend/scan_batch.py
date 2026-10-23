"""Bounded scheduled scanner; never grants identity or operation access."""
import asyncio
import os
import time
from motor.motor_asyncio import AsyncIOMotorClient
from web_workers import scan_document_once


async def main():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'], serverSelectionTimeoutMS=5000, tz_aware=True)
    try:
        db = client[os.environ['DB_NAME']]
        await db.command('ping')
        deadline = time.monotonic() + 600
        processed = 0
        while time.monotonic() < deadline and processed < 100:
            result = await scan_document_once(db)
            if not result['processed']:
                if result.get('reason'): raise RuntimeError(result['reason'])
                break
            processed += 1
        print(f'SCAN_BATCH_PROCESSED={processed}', flush=True)
    finally:
        client.close()


if __name__ == '__main__':
    asyncio.run(main())
