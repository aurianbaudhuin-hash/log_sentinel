"""Benchmark: custom bubble sort vs. Python's built-in sorted().

Compares both approaches for ranking IP addresses by request count,
using data extracted from a real (or generated) log file.

Usage:
    python benchmark.py <logfile>
"""

import argparse
import copy
import time

from logsentinel.parser import parse_log_file
from logsentinel.stats import bubble_sort


def count_requests_by_ip(file_path: str) -> list[tuple[str, int]]:
    """Parse a log file and count requests per IP address.

    Args:
        file_path: path to the log file to read.

    Returns:
        A list of (ip, count) tuples, in no particular order.
    """
    ip_counts: dict[str, int] = {}
    for entry, _raw_line in parse_log_file(file_path):
        if entry is None:
            continue
        ip_counts[entry.ip] = ip_counts.get(entry.ip, 0) + 1
    return list(ip_counts.items())


def time_sort(sort_fn, data: list[tuple[str, int]]) -> tuple[float, list]:
    """Time how long a sort function takes on a copy of the given data.

    Args:
        sort_fn: a callable that takes a list and returns a sorted list.
        data: the data to sort. A copy is passed to sort_fn so the
            original is left untouched for subsequent runs.

    Returns:
        A tuple (elapsed_seconds, sorted_result).
    """
    data_copy = copy.deepcopy(data)
    start = time.perf_counter()
    result = sort_fn(data_copy)
    elapsed = time.perf_counter() - start
    return elapsed, result


def sorted_by_count(items: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """Sort (ip, count) pairs by count, descending, using sorted().

    Args:
        items: a list of (ip, count) tuples to sort.

    Returns:
        The sorted list, in descending order of count.
    """
    return sorted(items, key=lambda pair: pair[1], reverse=True)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        The parsed arguments as an argparse.Namespace.
    """
    parser = argparse.ArgumentParser(
        description="Benchmark bubble_sort against sorted() on log data."
    )
    parser.add_argument("logfile", help="Path to the log file to use as input")
    return parser.parse_args()


def main() -> None:
    """Run the benchmark and print a summary."""
    args = parse_args()

    print(f"Reading and counting requests from '{args.logfile}'...")
    ip_counts = count_requests_by_ip(args.logfile)
    print(f"Distinct IP addresses: {len(ip_counts)}")

    bubble_time, bubble_result = time_sort(bubble_sort, ip_counts)
    native_time, native_result = time_sort(sorted_by_count, ip_counts)

    print()
    print(f"bubble_sort (custom):  {bubble_time:.4f} seconds")
    print(f"sorted() (built-in):   {native_time:.4f} seconds")

    if bubble_result == native_result:
        print("\nBoth approaches produced identical rankings.")
    else:
        print("\nWarning: the two approaches produced different rankings.")

    if native_time > 0:
        ratio = bubble_time / native_time
        print(f"\nbubble_sort was {ratio:.1f}x slower than sorted() on this dataset.")


if __name__ == "__main__":
    main()
