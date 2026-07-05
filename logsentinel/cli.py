"""Command-line interface for logsentinel.

Handles argument parsing, report display, and export to JSON/CSV.
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from typing import Optional

from logsentinel.parser import parse_log_file
from logsentinel.stats import Report, build_report

DATE_ARG_FORMAT = "%d/%b/%Y"


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Define and parse command-line arguments.

    Args:
        argv: list of argument strings to parse. Defaults to None,
            in which case argparse reads from sys.argv.

    Returns:
        The parsed arguments as an argparse.Namespace.
    """
    parser = argparse.ArgumentParser(
        prog="logsentinel",
        description="Analyze Apache combined log files.",
    )
    parser.add_argument("logfile", help="Path to the log file to analyze")
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top IPs to display (default: 10)",
    )
    parser.add_argument(
        "--export",
        choices=["json", "csv"],
        default=None,
        help="Export the report as JSON or CSV",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path for the export (default: static/report.json or .csv)",
    )
    parser.add_argument(
        "--from",
        dest="date_from",
        default=None,
        help="Only include entries from this date (format: DD/Mon/YYYY)",
    )
    parser.add_argument(
        "--to",
        dest="date_to",
        default=None,
        help="Only include entries up to this date (format: DD/Mon/YYYY)",
    )
    return parser.parse_args(argv)


def _parse_date_arg(date_str: Optional[str], arg_name: str) -> Optional[datetime]:
    """Convert a --from/--to string argument into a timezone-aware datetime.

    Args:
        date_str: the raw date string provided by the user, or None.
        arg_name: the name of the argument, used for error messages.

    Returns:
        A timezone-aware (UTC) datetime, or None if date_str is None.

    Raises:
        SystemExit: if date_str does not match the expected format.
    """
    if date_str is None:
        return None
    try:
        naive_datetime = datetime.strptime(date_str, DATE_ARG_FORMAT)
        return naive_datetime.replace(tzinfo=timezone.utc)
    except ValueError:
        print(
            f"Error: invalid date format for {arg_name}. "
            f"Expected format: DD/Mon/YYYY",
            file=sys.stderr,
        )
        sys.exit(1)


def export_json(report: Report, path: str = "static/report.json") -> None:
    """Export a report to a JSON file.

    Args:
        report: the report to export.
        path: destination file path.
    """
    report_dict = {
        "valid_count": report.valid_count,
        "ignored_count": report.ignored_count,
        "status_code_count": report.status_code_count,
        "hour_counter": sorted(report.hour_counter.items()),
        "error_ips": report.error_ips,
        "average_size": report.average_size,
        "top_ips": report.top_ips,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, default=str, indent=4)


def export_csv(report: Report, path: str = "static/report.csv") -> None:
    """Export a report to a CSV file.

    Args:
        report: the report to export.
        path: destination file path.
    """
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Valid log entries", report.valid_count])
        writer.writerow(["Ignored log entries", report.ignored_count])
        writer.writerow(["Average size of requests", report.average_size])
        writer.writerow(
            ["Top IP addresses by number of requests", ", ".join(report.top_ips)]
        )
        writer.writerow([])

        writer.writerow(["Status code counts"])
        for status_code, count in report.status_code_count.items():
            writer.writerow([status_code, count])
        writer.writerow([])

        writer.writerow(["Requests per hour"])
        for hour in range(24):
            count = report.hour_counter.get(hour, 0)
            writer.writerow([hour, count])
        writer.writerow([])

        writer.writerow(["Error IP addresses"])
        for ip, count in report.error_ips.items():
            writer.writerow([ip, count])


def main(argv: Optional[list[str]] = None) -> None:
    """Entry point for the logsentinel CLI.

    Args:
        argv: list of argument strings to parse. Defaults to None,
            in which case argparse reads from sys.argv.
    """
    args = parse_args(argv)

    date_from = _parse_date_arg(args.date_from, "--from")
    date_to = _parse_date_arg(args.date_to, "--to")

    try:
        entries = parse_log_file(args.logfile)
        report = build_report(entries, date_from=date_from, date_to=date_to, n=args.top)
    except FileNotFoundError:
        print(f"Error: file not found '{args.logfile}'", file=sys.stderr)
        sys.exit(1)

    report.print()

    if args.export == "json":
        export_json(report, args.output or "static/report.json")
    elif args.export == "csv":
        export_csv(report, args.output or "static/report.csv")


if __name__ == "__main__":
    main()