"""Parsing of log lines in Apache 'combined log' format."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator, Optional

LOG_PATTERN = re.compile(
    r"(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] "
    r'"(?P<method>\S+) (?P<path>\S+) \S+" '
    r"(?P<status>\d{3}) (?P<size>\d+|-)"
)

DATE_FORMAT = "%d/%b/%Y:%H:%M:%S %z"


@dataclass
class LogEntry:
    """Represents a single validated and typed log entry."""

    ip: str
    timestamp: datetime
    method: str
    path: str
    status: int
    size: int

    def print(self) -> None:
        """Print the entry in a human-readable format for debugging."""
        print(
            f"IP: {self.ip}, Timestamp: {self.timestamp}, "
            f"Method: {self.method}, Path: {self.path}, "
            f"Status: {self.status}, Size: {self.size}"
        )


def parse_line(line: str) -> Optional[LogEntry]:
    """Parse a single log line.

    Args:
        line: a raw line from the log file.

    Returns:
        A LogEntry if the line is valid, otherwise None. Never
        raises an exception: a malformed line is a normal case,
        not a fatal error.
    """
    match = LOG_PATTERN.match(line)
    if not match:
        return None

    groups = match.groupdict()

    try:
        groups["timestamp"] = datetime.strptime(groups["timestamp"], DATE_FORMAT)
    except ValueError:
        return None

    groups["status"] = int(groups["status"])
    groups["size"] = 0 if groups["size"] == "-" else int(groups["size"])

    return LogEntry(**groups)


def parse_log_file(file_path: str) -> Iterator[tuple[Optional[LogEntry], str]]:
    """Parse a log file line by line, without loading it into memory.

    Args:
        file_path: path to the log file to read.

    Yields:
        A tuple (entry, raw_line) for each line in the file, where
        entry is None if the line is malformed.

    Raises:
        FileNotFoundError: if the file doesn't exist. This exception
            is not caught here: it's up to the caller (cli.py) to
            handle it and display a clear message to the user.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            log_entry = parse_line(line)
            yield log_entry, line