"""Generate a fake Apache 'combined log' file for testing and benchmarking."""

import argparse
import random
from datetime import datetime, timedelta, timezone

METHODS = ["GET", "POST", "PUT", "DELETE"]
SUCCESS_CODES = [200, 201]
ERROR_CODES = [400, 401, 403, 404, 500, 502, 503]
DATE_FORMAT = "%d/%b/%Y:%H:%M:%S +0000"

DEFAULT_LINE_COUNT = 50_000
DEFAULT_OUTPUT_PATH = "static/fake_logs.txt"
DEFAULT_MALFORMED_RATIO = 0.02

MALFORMED_LINES = [
    "this is not a valid log line\n",
    "GET /index.html HTTP/1.1\n",
    "192.168.1.1 - - incomplete entry\n",
    "\n",
]


def random_ip() -> str:
    """Generate a random IPv4 address.

    Returns:
        A string representing a random IPv4 address.
    """
    return ".".join(str(random.randint(1, 255)) for _ in range(4))


def random_timestamp() -> str:
    """Generate a random timestamp string in Apache combined log format.

    Returns:
        A timestamp string, e.g. '14/May/2023:10:23:45 +0000'.
    """
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    random_offset = timedelta(seconds=random.randint(0, 4 * 365 * 24 * 3600))
    return (start + random_offset).strftime(DATE_FORMAT)


def generate_fake_line() -> str:
    """Generate a single fake log line in Apache combined log format.

    Returns:
        A string representing one valid log line, matching the
        format expected by logsentinel.parser.LOG_PATTERN.
    """
    ip_address = random_ip()
    timestamp = random_timestamp()
    method = random.choice(METHODS)
    path = f"/api/v1/resource/{random.randint(1, 100)}"
    if random.random() < 0.99:
        status_code = random.choice(SUCCESS_CODES)
    else:
        status_code = random.choice(ERROR_CODES)
    size = random.randint(0, 5000)
    size_field = "-" if size == 0 else str(size)

    return (
        f'{ip_address} - - [{timestamp}] '
        f'"{method} {path} HTTP/1.1" {status_code} {size_field}'
    )


def generate_malformed_line() -> str:
    """Generate a single malformed log line.

    Returns:
        A string representing one line that does not match the
        expected log format, used to test parser robustness.
    """
    return random.choice(MALFORMED_LINES)


def write_log_file(
    num_lines: int,
    output_path: str = DEFAULT_OUTPUT_PATH,
    malformed_ratio: float = DEFAULT_MALFORMED_RATIO,
) -> None:
    """Write a specified number of fake log lines to a file.

    A fraction of the generated lines are intentionally malformed,
    to allow testing that the parser correctly ignores invalid
    lines without crashing.

    Args:
        num_lines: number of log lines to generate.
        output_path: destination file path.
        malformed_ratio: fraction of lines that should be malformed,
            between 0.0 and 1.0.
    """
    with open(output_path, "w", encoding="utf-8") as log_file:
        for _ in range(num_lines):
            if random.random() < malformed_ratio:
                line = generate_malformed_line()
            else:
                line = generate_fake_line() + "\n"
            log_file.write(line)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        The parsed arguments as an argparse.Namespace.
    """
    parser = argparse.ArgumentParser(
        description="Generate a fake log file with a specified line count."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_LINE_COUNT,
        help=f"Number of lines to generate (default: {DEFAULT_LINE_COUNT})",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_PATH,
        help=f"Output file path (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--malformed-ratio",
        type=float,
        default=DEFAULT_MALFORMED_RATIO,
        help=(
            "Fraction of lines that are intentionally malformed, "
            f"between 0.0 and 1.0 (default: {DEFAULT_MALFORMED_RATIO})"
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    write_log_file(args.count, args.output, args.malformed_ratio)
    print(f"{args.count} lines generated in {args.output}")