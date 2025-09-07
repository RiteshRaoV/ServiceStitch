# orchestration/nats_manager.py
import asyncio
from nats.aio.client import Client as NATS

async def publish(subject: str, payload: bytes, url: str = "nats://127.0.0.1:4222"):
    nc = NATS()
    await nc.connect(url)
    await nc.publish(subject, payload)
    await nc.drain()
    await nc.close()

async def subscribe(subject: str, cb, url: str = "nats://127.0.0.1:4222"):
    nc = NATS()
    await nc.connect(url)
    async def _cb(msg):
        await cb(msg)
    await nc.subscribe(subject, cb=_cb)
    return nc  # caller can keep running (remember to close)
