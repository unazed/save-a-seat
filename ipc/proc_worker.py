import threading
import multiprocessing
import queue
import os

"""
TODO:
    WorkerThreadPool:
        - load balancing heuristics, or double-ended queue
        - implement `delegate` based on heuristics
    WorkerThread:
        - implement asynchronous loop to deal with influx of jobs,
          e.g. load all courses, send email, etc.
"""


class WorkerThread:
    def __init__(self):
        pass


class WorkerThreadPool:
    def __init__(self, size):
        self.thread_array = [WorkerThread() for _ in range(size)]
        self.thread_stats = []

    def delegate(self, result_queue):
        pass


class ProcessWorker:
    def __init__(self, *, thread_pool_size=os.cpu_count(), start_proc=True):
        self.process = None
        self.master_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        self.thread_pool_size = thread_pool_size
        if start_proc:
            self.start_working()

    def worker(self, pipe):
        thread_pool = WorkerThreadPool(self.thread_pool_size)
        while (job := self.receive_job()):
            thread_pool.delegate(job, self.result_queue)

    def receive_job(self):
        return self.master_queue.get()

    def place_job(self, job, priority):
        return self.master_queue.put((priority, job))

    def start_working(self):
        self.process = multiprocessing.Process(target=self.worker,
                args=(self.slave,))
        self.process.start()
