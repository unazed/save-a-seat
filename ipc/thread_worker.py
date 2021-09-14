from dataclasses import dataclass
from queue import PriorityQueue
from typing import Any
import threading
import uuid


"""
TODO:
    ThreadWorker:
        - implement `handle_proc_results` to bridge WorkerThread results to
          the communication channel between it and the server handler
"""


@dataclass
class Job:
    action: str
    client_index: int
    additional: Any = None


LOW_PRIORITY = 3
MEDIUM_PRIORITY = 2 
HIGH_PRIORITY = 1


class ProxyDict(dict):
    def __init__(self, *args, priority=LOW_PRIORITY, **kwargs):
        super().__init__(*args, **kwargs)
        self.priority = priority

    def __lt__(self, other):
        return self.priority < other.priority


class ThreadWorker: 
    def __init__(self, server, proc_worker, *, start_thread=True):
        self.server = server
        self.proc_worker = proc_worker
        self.thread = None
        self.out_queue = PriorityQueue()
        if start_thread:
            self.start_working()

    def handle_result(self, result):
        priority, job, result = result
        job = job['data']
        client = self.server.clients[job.client_index]
        client.send({
            "status": False,
            "action": job.action,
            "data": result
            }, pass_action=False)

    def worker(self):
        while True:
            if not self.proc_worker.result_queue.empty():
                self.handle_result(self.proc_worker.result_queue.get())
            if not self.out_queue.empty():
                self.proc_worker.place_job(self.out_queue.get())

    def start_working(self):
        self.thread = threading.Thread(target=self.worker)
        self.thread.start()

    def place_job(self, job, *, priority=LOW_PRIORITY):
        self.out_queue.put((priority, ProxyDict({
            "id": (tid := uuid.uuid1().hex),
            "data": job
            }, priority=priority)))
        return tid
