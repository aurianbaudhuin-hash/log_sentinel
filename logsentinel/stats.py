"""Statistics and reporting for parsed log entries."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator, Optional

from logsentinel.parser import LogEntry


@dataclass
class Report:
    """Represents a report generated from log entries."""

    valid_count: int = 0
    ignored_count: int = 0
    status_code_count: dict = field(default_factory=dict)
    hour_counter: dict = field(default_factory=dict)
    error_ips: dict = field(default_factory=dict)
    average_size: float = 0
    top_ips: list = field(default_factory=list)

    def print(self) -> None:
        """Print the report in a human-readable format."""
        print(f"Valid log entries: {self.valid_count}")
        print(f"Ignored log entries: {self.ignored_count}")

        print("Status code counts:")
        for status_code, count in self.status_code_count.items():
            print(f"  {status_code}: {count}")

        print("Requests per hour:")
        for hour in range(24):
            count = self.hour_counter.get(hour, 0)
            print(f"{hour:02d}h: {count}")

        print("Error IP addresses:")
        for ip, count in self.error_ips.items():
            print(f"  {ip}: {count}")

        print(f"Average size of requests: {self.average_size:.2f} bytes")

        print(f"Top {len(self.top_ips)} IP addresses by number of requests:")
        for ip in self.top_ips:
            print(f"  {ip}")


def bubble_sort(items: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """Sort a list of (key, count) pairs by count, in descending order.

    Custom sorting implementation, used instead of the built-in
    sorted() to rank IPs by number of requests.

    Args:
        items: a list of (key, count) tuples to sort.

    Returns:
        The same list, sorted by count in descending order.
    """
    n = len(items)
    is_sorted = False
    while not is_sorted:
        is_sorted = True
        for i in range(n - 1):
            if items[i][1] < items[i + 1][1]:
                items[i], items[i + 1] = items[i + 1], items[i]
                is_sorted = False
    return items


def sort_entries_by_number_of_requests(
    entries: Iterator[LogEntry],
) -> list[tuple[str, int]]:
    """Count requests per IP and sort the result by count.

    Args:
        entries: an iterable of LogEntry objects.

    Returns:
        A list of (ip, count) tuples, sorted by count in descending
        order.
    """
    ip_addresses: dict[str, int] = {}
    for entry in entries:
        if entry is None:
            continue
        ip_addresses[entry.ip] = ip_addresses.get(entry.ip, 0) + 1
    return bubble_sort(list(ip_addresses.items()))


def build_report(
    entries: Iterator[tuple[Optional[LogEntry], str]],
    date_from: Optional[datetime],
    date_to: Optional[datetime],
    n: int,
) -> Report:
    """Build a full report from a stream of parsed log entries.

    Args:
        entries: an iterable of (entry, raw_line) tuples, typically
            produced by parser.parse_log_file(). entry is None if
            the corresponding line was malformed.
        date_from: if provided, entries before this date are excluded.
        date_to: if provided, entries after this date are excluded.
        n: number of top IPs to include in the report.

    Returns:
        A Report summarizing the filtered entries.
    """
    report = Report()

    filtered_entries = []
    for entry, _raw_line in entries:
        if entry is None:
            report.ignored_count += 1
            continue
        if date_from and entry.timestamp < date_from:
            continue
        if date_to and entry.timestamp > date_to:
            continue
        filtered_entries.append(entry)

    top_ips = sort_entries_by_number_of_requests(filtered_entries)
    report.top_ips = [ip for ip, _count in top_ips[:n]]

    total_sized_entries = 0
    for entry in filtered_entries:
        report.valid_count += 1

        hour = entry.timestamp.hour
        report.hour_counter[hour] = report.hour_counter.get(hour, 0) + 1

        report.status_code_count[entry.status] = (
            report.status_code_count.get(entry.status, 0) + 1
        )

        if entry.status >= 400:
            report.error_ips[entry.ip] = report.error_ips.get(entry.ip, 0) + 1

        report.average_size += entry.size
        total_sized_entries += 1

    if total_sized_entries > 0:
        report.average_size /= total_sized_entries

    return report