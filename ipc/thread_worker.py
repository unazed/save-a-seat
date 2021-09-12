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


LOW_PRIORITY = 3
MEDIUM_PRIORITY = 2 
HIGH_PRIORITY = 1


class ThreadWorker: 
    def __init__(self, server, proc_worker, *, start_thread=True):
        self.server = server
        self.proc_worker = proc_worker
        self.thread = None
        self.out_queue = PriorityQueue()
        if start_thread:
            self.start_working()

    def handle_result(self, result):
        print("in threadworker", result)

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
        print("placing job", job)
        self.out_queue.put((priority, {
            "id": (tid := uuid.uuid1().hex),
            "data": job
            }))
        return tid
