import time


class Stopwatch:
    def __init__(self):
        self.start = time.perf_counter()

    def __call__(self):
        stop = time.perf_counter()
        took = stop - self.start
        self.start = stop

        return f"{took:.3f}s"
