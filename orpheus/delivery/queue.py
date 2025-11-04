import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional


class DeliveryQueue:
    def __init__(self, max_workers: int = 2):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.enabled = max_workers > 1
        self._lock = threading.Lock()

    def submit(self, fn: Callable, *args, **kwargs):
        if not self.enabled:
            return fn(*args, **kwargs)
        with self._lock:
            return self.executor.submit(fn, *args, **kwargs)

    def shutdown(self, wait: bool = True):
        self.executor.shutdown(wait=wait)


delivery_queue = DeliveryQueue()
