# rubric corpus b03 — stateful class, low testability.
# Primary concern: hard-coded paths, singleton-ish globals, no seams.

import time


COUNTER_FILE = "/tmp/counter.txt"


class Counter:
    def __init__(self):
        try:
            with open(COUNTER_FILE) as f:
                self.n = int(f.read())
        except Exception:
            self.n = 0
        self.started = time.time()

    def inc(self):
        self.n = self.n + 1
        with open(COUNTER_FILE, "w") as f:
            f.write(str(self.n))
        return self.n

    def reset(self):
        self.n = 0
        with open(COUNTER_FILE, "w") as f:
            f.write("0")


_C = Counter()


def bump():
    return _C.inc()
