# orchestration/fault_injection.py
import random
import time

def maybe_delay(latency_ms: int):
    if latency_ms and latency_ms > 0:
        time.sleep(latency_ms / 1000.0)

def maybe_fail(failure_rate: float):
    if failure_rate and random.random() < failure_rate:
        raise RuntimeError("Injected fault")
