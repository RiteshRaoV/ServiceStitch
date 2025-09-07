# orchestration/load_tester.py
import asyncio
import time
import httpx

async def worker(target: str, q: asyncio.Queue):
    async with httpx.AsyncClient() as client:
        while True:
            item = await q.get()
            if item is None:
                break
            method, url, data = item
            try:
                if method == "GET":
                    r = await client.get(url, timeout=10)
                else:
                    r = await client.request(method, url, json=data, timeout=10)
                print(f"[load] {method} {url} -> {r.status_code}")
            except Exception as e:
                print(f"[load] error {method} {url} -> {e}")
            finally:
                q.task_done()

async def run_load(target_url: str, method: str = "GET", rps: int = 10, duration: int = 10, concurrency: int = 10, payload=None):
    """
    target_url: full URL (http://localhost:8001/projects)
    rps: requests per second
    duration: seconds
    concurrency: number of worker tasks
    """
    q = asyncio.Queue()
    workers = [asyncio.create_task(worker(target_url, q)) for _ in range(concurrency)]

    start = time.time()
    interval = 1.0 / rps
    sent = 0
    try:
        while time.time() - start < duration:
            # enqueue one request
            await q.put((method, target_url, payload))
            sent += 1
            await asyncio.sleep(interval)
    finally:
        # stop workers
        for _ in workers:
            await q.put(None)
        await q.join()
        for w in workers:
            w.cancel()
    print(f"[load] finished sending {sent} requests")

def start_sync(target_url: str, method: str = "GET", rps: int = 10, duration: int = 10, concurrency: int = 10, payload=None):
    asyncio.run(run_load(target_url, method, rps, duration, concurrency, payload))
    