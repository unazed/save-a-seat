import asyncio
import threading
import multiprocessing
import queue
import os
import inspect


class WorkerThread:
    def __init__(self, action_map, post_action_map, callback_map,
            result_queue, job_queue, *, start_thread=True):
        self.thread = None
        self.result_queue = result_queue
        self.job_queue = job_queue

        self.action_map = action_map
        self.post_action_map = post_action_map
        self.callback_map = callback_map

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
        action = job[1]['data'].action

        if (callback := self.callback_map.get(action)) is not None:
            self.result_queue.put((-1, job[1], (callback, result)))

        self.result_queue.put(job + (result,))

        if (action := self.post_action_map.get(action)) \
                is not None:
            if inspect.iscoroutinefunction(action):
                loop = asyncio.new_evet_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(action(self, result))
            elif action.__name__ == "<lambda>":  # dodgy
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                fn, args = action(self, result)
                self.result_queue.put(
                        job + (loop.run_until_complete(fn(*args)),))
            else:
                action(self, result)

    def worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        tasks = []
        while True:
            job = self.receive_job()
            if job is not None:
                priority, task = job
                if task['data'].additional is not None:
                    tasks.append((job, loop.create_task(
                                self.action_map[task['data'].action](
                                    self, task['data'].additional))))
                else:
                    tasks.append((job, loop.create_task(
                                self.action_map[task['data'].action](self))))
                continue
            elif not tasks:
                continue
            loop.run_until_complete(asyncio.gather(
                *list(task[1] for task in tasks \
                        if task is not None and not task[1].done())))
            for idx, (tid, task) in enumerate(tasks):
                if task.done():
                    tasks.remove((tid, task))
                    self.finish_job(tid, task.result())


class WorkerThreadPool:
    def __init__(self, action_map, post_action_map, callback_map,
            result_queue, size):
        self.job_queue = queue.PriorityQueue()
        self.result_queue = result_queue
        self.thread_array = [WorkerThread(action_map, post_action_map,
            callback_map, result_queue, self.job_queue) for _ in range(size)]

    def delegate(self, job):
        self.job_queue.put(job)


class ProcessWorker:
    def __init__(self, action_map, post_action_map, callback_map, *,
            thread_pool_size=os.cpu_count(), start_proc=True):
        self.process = None
        
        self.master_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()

        self.thread_pool_size = thread_pool_size

        self.action_map = action_map
        self.post_action_map = post_action_map
        self.callback_map = callback_map

        if start_proc:
            self.start_working()

    def worker(self):
        thread_pool = WorkerThreadPool(self.action_map, self.post_action_map,
                self.callback_map, self.result_queue, self.thread_pool_size)
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
