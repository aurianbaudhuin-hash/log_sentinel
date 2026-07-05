"""Tests for logsentinel.stats."""

from datetime import datetime, timezone

from logsentinel.parser import LogEntry
from logsentinel.stats import build_report, bubble_sort, sort_entries_by_number_of_requests


def make_entry(ip="1.1.1.1", status=200, size=100, hour=12, path="/index.html"):
    return LogEntry(
        ip=ip,
        timestamp=datetime(2026, 1, 1, hour, 0, 0, tzinfo=timezone.utc),
        method="GET",
        path=path,
        status=status,
        size=size,
    )


# bubble_sort

def test_bubble_sort_descending_order():
    items = [("a", 3), ("b", 10), ("c", 1)]
    result = bubble_sort(items)
    assert result == [("b", 10), ("a", 3), ("c", 1)]


def test_bubble_sort_empty_list():
    assert bubble_sort([]) == []


def test_bubble_sort_single_item():
    assert bubble_sort([("a", 5)]) == [("a", 5)]


# sort_entries_by_number_of_requests

def test_sort_entries_counts_and_orders_by_ip():
    entries = [
        make_entry(ip="1.1.1.1"),
        make_entry(ip="1.1.1.1"),
        make_entry(ip="2.2.2.2"),
    ]
    result = sort_entries_by_number_of_requests(entries)
    assert result[0] == ("1.1.1.1", 2)
    assert result[1] == ("2.2.2.2", 1)


# build_report: basic counts
def test_build_report_counts_valid_and_ignored():
    entries = [(make_entry(), "raw"), (None, "bad line"), (make_entry(), "raw")]
    report = build_report(entries, date_from=None, date_to=None, n=1)
    assert report.valid_count == 2
    assert report.ignored_count == 1


# status codes / hour counter

def test_build_report_status_code_distribution():
    entries = [
        (make_entry(status=200), "raw"),
        (make_entry(status=200), "raw"),
        (make_entry(status=404), "raw"),
    ]
    report = build_report(entries, None, None, n=1)
    assert report.status_code_count[200] == 2
    assert report.status_code_count[404] == 1


def test_build_report_hour_distribution():
    entries = [(make_entry(hour=5), "raw"), (make_entry(hour=5), "raw"), (make_entry(hour=20), "raw")]
    report = build_report(entries, None, None, n=1)
    assert report.hour_counter[5] == 2
    assert report.hour_counter[20] == 1
    assert 3 not in report.hour_counter


# error IPs

def test_build_report_error_ips_tracked():
    entries = [
        (make_entry(ip="1.1.1.1", status=404), "raw"),
        (make_entry(ip="1.1.1.1", status=200), "raw"),
        (make_entry(ip="2.2.2.2", status=200), "raw"),
    ]
    report = build_report(entries, None, None, n=1)
    assert "1.1.1.1" in report.error_ips
    assert "2.2.2.2" not in report.error_ips


# average size

def test_build_report_average_size():
    entries = [(make_entry(size=100), "raw"), (make_entry(size=200), "raw")]
    report = build_report(entries, None, None, n=1)
    assert report.average_size == 150.0


# date filtering

def test_build_report_filters_by_date_from():
    early = make_entry(hour=5)
    late = make_entry(hour=20)
    entries = [(early, "raw"), (late, "raw")]
    date_from = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    report = build_report(entries, date_from=date_from, date_to=None, n=1)
    assert report.valid_count == 1


def test_build_report_filters_by_date_to():
    early = make_entry(hour=5)
    late = make_entry(hour=20)
    entries = [(early, "raw"), (late, "raw")]
    date_to = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    report = build_report(entries, date_from=None, date_to=date_to, n=1)
    assert report.valid_count == 1


# top N

def test_build_report_top_ips_order():
    entries = [
        (make_entry(ip="1.1.1.1"), "raw"),
        (make_entry(ip="1.1.1.1"), "raw"),
        (make_entry(ip="1.1.1.1"), "raw"),
        (make_entry(ip="2.2.2.2"), "raw"),
    ]
    report = build_report(entries, None, None, n=1)
    assert report.top_ips == ["1.1.1.1"]


def test_build_report_top_n_larger_than_available_ips():
    entries = [(make_entry(ip="1.1.1.1"), "raw")]
    report = build_report(entries, None, None, n=5)
    assert report.top_ips == ["1.1.1.1"]