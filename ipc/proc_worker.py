import asyncio
import threading
import multiprocessing
import queue
import os


class WorkerThread:
    def __init__(self, action_map, result_queue, job_queue,
            *, start_thread=True):
        self.thread = None
        self.result_queue = result_queue
        self.job_queue = job_queue
        self.action_map = action_map
        if start_thread:
            self.start_working()

    def start_working(self):
        self.thread = threading.Thread(target=self.worker)
        self.thread.start()

    def receive_job(self):
        try:
            return self.job_queue.get_nowait()
        except queue.Empty:
            return

    def finish_job(self, job, result):
        self.result_queue.put(job + (result,))

    def worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while True:
            job = self.receive_job()
            if job is not None:
                print(job)
                self.finish_job(job, {"data": "roflmao"})


class WorkerThreadPool:
    def __init__(self, action_map, result_queue, size):
        self.job_queue = queue.PriorityQueue()
        self.result_queue = result_queue
        self.thread_array = [WorkerThread(action_map, result_queue,
                    self.job_queue) for _ in range(size)]

    def delegate(self, job):
        print("inserting job", job)
        self.job_queue.put(job)


class ProcessWorker:
    def __init__(self, action_map, *, thread_pool_size=os.cpu_count(),
            start_proc=True):
        self.process = None
        self.master_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        self.thread_pool_size = thread_pool_size
        self.action_map = action_map
        if start_proc:
            self.start_working()

    def worker(self):
        thread_pool = WorkerThreadPool(
                self.action_map, self.result_queue, self.thread_pool_size)
        while True:
            job = self.receive_job()
            if job is not None:
                thread_pool.delegate(job)

    def get_result(self):
        try:
            return self.result_queue.get_nowait()
        except queue.Empty:
            return

    def receive_job(self):
        try:
            return self.master_queue.get_nowait()
        except queue.Empty:
            return

    def place_job(self, job):
        return self.master_queue.put(job)

    def start_working(self):
        self.process = multiprocessing.Process(target=self.worker)
        self.process.start()
