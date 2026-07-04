import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator


@dataclass
class LogEntry:
    """Represents a single validated and typed log entry."""
    ip: str
    timestamp: datetime
    method: str
    path: str
    status: int
    size: int
    
    def print(self):
        """Print the entry in a human-readable format for debugging."""
        print(f"IP: {self.ip}, Timestamp: {self.timestamp}, Method: {self.method}, Path: {self.path}, Status: {self.status}, Size: {self.size}")
    
    
regex_sequence = r"(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] \"(?P<method>\S+) (?P<path>\S+) \S+\" (?P<status>\d{3}) (?P<size>\d+|-)"


def parse_line(line: str) -> LogEntry:
    """Parse a single log line.

    Args:
        line: a raw line from the log file.

    Returns:
        A LogEntry if the line is valid, otherwise None.
        Never raises an exception: a malformed line is a normal
        case, not a fatal error.
    """
    match = re.match(regex_sequence, line)
    if not match:
        return None
    groups = match.groupdict()
    try:
        groups['timestamp'] = datetime.strptime(groups['timestamp'], "%d/%b/%Y:%H:%M:%S %z")
    except ValueError:
        return None
    groups['status'] = int(groups['status'])
    if groups['size'] == '-':
        groups['size'] = 0
    else:
        groups['size'] = int(groups['size'])

    return LogEntry(**groups)

def parse_log_file(file_path: str) -> Iterator[tuple[LogEntry | None, str]]:
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
    with open(file_path, 'r') as file:
        for line in file:
            log_entry = parse_line(line)
            yield log_entry, line

