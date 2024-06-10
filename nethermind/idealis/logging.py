import atexit
import queue
import threading
import time
from dataclasses import dataclass
from logging import Handler, LogRecord

import requests


@dataclass(slots=True)
class LokiLogLine:
    labels: dict[str, str]
    timestamp_ns: int
    message: str

    def label_key(self):
        sorted_keys = sorted(self.labels.keys())

        return "__".join([f"{key}:{self.labels[key]}" for key in sorted_keys])


@dataclass(slots=True)
class LabelStream:
    labels: dict[str, str]
    entries: list[list[str]]

    def json_dict(self):
        return {"stream": self.labels, "values": self.entries}

    def add_log(self, loki_log: LokiLogLine):
        self.entries.append([str(loki_log.timestamp_ns), loki_log.message])


class LokiLogStream:
    """
    Represent the Streams of a loki entry. When writing JSON, the stream looks like the following:

    {
        "streams": [
            {"labels": {"application": "app_name}, "entries": [[log_timestamp_ns, <message>], ...]}
        ]
    }

    This stream dataclass contains the labels added, and converts python LogRecords into this loki format
    """

    def __init__(self):
        self.streams = {}

    streams: dict[str, LabelStream]

    def add_loki_log(self, log_line: LokiLogLine):
        label_key = log_line.label_key()

        if label_key not in self.streams:
            self.streams.update({label_key: LabelStream(labels=log_line.labels, entries=[])})

        self.streams[label_key].add_log(log_line)

    def json_dict(self):
        return {"streams": [stream.json_dict() for stream in self.streams.values()]}


# TODO:  Clean up this clusterfuck...
class LokiLoggerHandler(Handler):
    loki_url: str
    post_headers = {"Content-type": "application/json"}

    logger_labels: dict[str, str]

    def __init__(
        self,
        loki_url,
        write_delay: int = 10,
        logger_labels: dict[str, str] | None = None,
    ):
        super().__init__()

        self.loki_url = loki_url
        self.logger_labels = logger_labels or {}
        self.write_delay = write_delay

        self._buffer = queue.Queue()
        self._request_session = requests.session()
        self._flush_thread = threading.Thread(target=self._flush, daemon=True)

        self._flush_thread.start()

    def emit(self, record: LogRecord):
        self._buffer.put(
            LokiLogLine(labels=self.logger_labels, timestamp_ns=int(record.created * 1e9), message=self.format(record))
        )

    def _flush(self):
        atexit.register(self._send)

        flushing = False
        while True:
            if not flushing and not self._buffer.empty():
                flushing = True
                self._send()
                flushing = False
            else:
                time.sleep(self.write_delay)

    def _send(self):
        loki_stream = LokiLogStream()

        while not self._buffer.empty():
            loki_log_line: LokiLogLine = self._buffer.get()
            loki_stream.add_loki_log(loki_log_line)

        try:
            response = self._request_session.post(
                self.loki_url, json=loki_stream.json_dict(), headers=self.post_headers
            )
            response.raise_for_status()
            response.close()

        except requests.RequestException as e:
            raise RuntimeError(f"Error Writing Logs to Loki:  {e}")

    def write(self, message):
        self.emit(message.record)
