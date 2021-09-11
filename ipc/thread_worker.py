from dataclasses import dataclass
from queue import PriorityQueue
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


class ThreadWorker:
    LOW_PRIORITY = 3
    MEDIUM_PRIORITY = 2 
    HIGH_PRIORITY = 1
    
    def __init__(self, server, proc_worker, *, start_thread=True):
        self.server = server
        self.proc_worker = proc_worker
        self.thread = None
        self.out_queue = PriorityQueue()
        if start_thread:
            self.start_working()

    def handle_proc_results(self, results):
        pass

    def worker(self):
        while True:
            self.handle_proc_results(self.proc_worker.get_new_results())
            if self.out_queue.not_empty:
                priority, job = self.out_queue.get()
                self.proc_worker.place_job(job, priority=priority)

    def start_working(self):
        self.thread = threading.Thread(target=self.worker)
        self.thread.start()

    def place_job(self, job, *, priority=ThreadWorker.LOW_PRIORITY):
        self.out_queue.put((priority, {
            "id": (tid := uuid.uuid1().hex),
            "data": job
            }))
        return tid
