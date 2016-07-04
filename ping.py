import time
import threading
import collections


class PingManager:
    # this ping manager assume ping function would be added in order
    # ie: newer function will always run later than the already added functions
    def __init__(self, interval=20):
        self.interval = interval
        self.list_queue = collections.deque()
        self.thread = threading.Thread(target=self.worker)
        self.thread.daemon = True
        self.thread.start()

    def worker(self):
        while True:
            # if self.list_queue is empty, check again in half interval
            if not self.list_queue:
                time.sleep(self.interval/2)
                continue

            target, task = self.list_queue.popleft()

            if not task.active:
                continue

            left = target - time.time()
            if left > 0:
                time.sleep(left)

            task.func()
            self.list_queue.append((time.time()+self.interval, task))

    def add(self, func):
        task = Task(func)
        self.list_queue.append((time.time()+self.interval, task))
        return task


class Task:
    def __init__(self, func):
        self.active = True
        self.func = func

    def cancel(self):
        self.active = False

ping = PingManager()
add = ping.add
