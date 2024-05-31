import asyncio
from collections import deque

class WorkerQueue:
    def __init__(self, worker_count:int = 10) -> None:
        self.worker_count = worker_count
        self.running = set()
        self.waiting = deque()

    @property
    def running_task_count(self):
        return len(self.running)
    
    def add_task(self, coro):
        if len(self.running) >= self.worker_count:
            self.waiting.append(coro)
        else:
            self._start_task(coro)

    def _start_task(self, coro):
        self.running.add(coro)
        asyncio.create_task(self._task(coro))

    async def _task(self, coro):
        try:
            return await coro
        finally:
            self.running.remove(coro)
            if self.waiting:
                coro2 = self.waiting.popleft()
                self._start_task(coro2)