import json
import os
from collections import deque

BUFFER_FILE = os.path.join(os.path.dirname(__file__), ".buffer.jsonl")


class RetryBuffer:
    def __init__(self, max_records: int = 3600):
        self.max_records = max_records
        self._buffer: deque[dict] = deque(maxlen=max_records)
        self._load()

    def _load(self):
        if os.path.exists(BUFFER_FILE):
            with open(BUFFER_FILE) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self._buffer.append(json.loads(line))

    def _save(self):
        with open(BUFFER_FILE, "w") as f:
            for record in self._buffer:
                f.write(json.dumps(record) + "\n")

    def add(self, payload: dict):
        self._buffer.append(payload)
        self._save()

    def peek_batch(self, n: int = 10) -> list[dict]:
        return list(self._buffer)[:n]

    def remove_batch(self, n: int = 10):
        for _ in range(min(n, len(self._buffer))):
            self._buffer.popleft()
        self._save()

    def __len__(self):
        return len(self._buffer)

    @property
    def is_empty(self):
        return len(self._buffer) == 0
