# servicestitch/orchestration/mock_service.py
import os
import json
import time
import random
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

try:
    import nats
except ImportError:
    nats = None

app = FastAPI()

# ---- Load environment variables ----
MOCK_ENDPOINTS = json.loads(os.getenv("MOCK_ENDPOINTS", "[]"))
NATS_SUBSCRIBE = json.loads(os.getenv("NATS_SUBSCRIBE", "[]"))
NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")

# ---- Global NATS publisher connection ----
nc_pub = None

# ---- HTTP Endpoint Handlers ----
for ep in MOCK_ENDPOINTS:
    path = ep["path"]
    method = ep.get("method", "GET").upper()
    response_data = ep.get("response", {"status": "ok"})
    delay = ep.get("delay", 0)
    failure_rate = ep.get("failure_rate", 0)
    nats_publish = ep.get("nats_publish", [])

    async def handler(req: Request, _resp=response_data, _delay=delay, _failure=failure_rate, _publish=nats_publish):
        # Simulate delay
        if _delay:
            time.sleep(_delay / 1000.0)

        # Simulate failure
        if _failure and random.random() < (_failure / 100.0):
            return JSONResponse(content={"error": "simulated failure"}, status_code=500)

        # Publish to NATS
        global nc_pub
        if _publish and nc_pub:
            for pub in _publish:
                subj = pub["subject"]
                data = pub.get("data", {})
                # replace template placeholders
                if isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, str) and v.startswith("{{") and v.endswith("}}"):
                            key = v[2:-2].strip()
                            data[k] = _resp.get(key)
                await nc_pub.publish(subj, json.dumps(data).encode())
                print(f"[NATS MOCK] Published to {subj}: {data}")

        return _resp

    app.add_api_route(path, handler, methods=[method])

# ---- NATS Subscriber ----
async def start_nats_subscriber():
    if not NATS_SUBSCRIBE or nats is None:
        return

    nc_sub = await nats.connect(NATS_URL)
    js = nc_sub.jetstream()

    async def handle_msg(msg):
        subj = msg.subject
        payload = msg.data.decode()
        print(f"[NATS MOCK] Received on {subj}: {payload}")

        for sub in NATS_SUBSCRIBE:
            if sub.get("subject") == subj:
                action = sub.get("action")
                if action:
                    method, path = action.split(" ", 1)
                    route = next((r for r in app.routes if r.path == path and method in r.methods), None)
                    if route:
                        req = Request(scope={"type": "http", "method": method, "path": path})
                        response = await route.endpoint(req)
                        print(f"[NATS MOCK] Triggered {method} {path}, got: {response}")

    for sub in NATS_SUBSCRIBE:
        await nc_sub.subscribe(sub["subject"], cb=handle_msg)

    print("[NATS MOCK] Subscribed to subjects:", [s["subject"] for s in NATS_SUBSCRIBE])

# ---- FastAPI startup events ----
@app.on_event("startup")
async def startup_event():
    global nc_pub

    # Start NATS publisher connection
    if nats is not None:
        nc_pub = await nats.connect(NATS_URL)
        print(f"[NATS MOCK] Connected to {NATS_URL} for publishing")

    # Start subscriber
    if NATS_SUBSCRIBE:
        asyncio.create_task(start_nats_subscriber())
