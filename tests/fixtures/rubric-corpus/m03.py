# rubric corpus m03 — stateful class, path injectable but no locking.
# Serviceable: path is an arg; still not thread-safe, no persistence error path.


class Counter:
    """Persistent integer counter backed by a plaintext file."""

    def __init__(self, path):
        self._path = path
        self._value = self._read_initial()

    def _read_initial(self):
        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                return int(fh.read().strip() or "0")
        except FileNotFoundError:
            return 0

    def inc(self):
        self._value += 1
        self._persist()
        return self._value

    def reset(self):
        self._value = 0
        self._persist()

    def _persist(self):
        with open(self._path, "w", encoding="utf-8") as fh:
            fh.write(str(self._value))
