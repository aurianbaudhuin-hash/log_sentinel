"""Tests for logsentinel.parser."""

from datetime import datetime, timezone, timedelta

import pytest

from logsentinel.parser import parse_line, parse_log_file, LogEntry


# Sample data

VALID_LINE = (
    '83.149.9.216 - - [17/May/2015:10:05:03 +0000] '
    '"GET /presentations/logstash-monitorama-2013/images/kibana-search.png '
    'HTTP/1.1" 200 203023\n'
)

VALID_LINE_DASH_SIZE = (
    '180.76.6.56 - - [20/May/2015:21:05:56 +0000] '
    '"GET /robots.txt HTTP/1.1" 200 -\n'
)

MALFORMED_LINE = "this is not a log line at all\n"

BAD_DATE_LINE = (
    '83.149.9.216 - - [not-a-date] '
    '"GET /index.html HTTP/1.1" 200 512\n'
)

BAD_STATUS_LINE = (
    '83.149.9.216 - - [17/May/2015:10:05:03 +0000] '
    '"GET /index.html HTTP/1.1" ABC 512\n'
)


# parse_line

def test_parse_line_valid_returns_log_entry():
    entry = parse_line(VALID_LINE)
    assert entry is not None
    assert isinstance(entry, LogEntry)


def test_parse_line_valid_fields_are_correct():
    entry = parse_line(VALID_LINE)
    assert entry.ip == "83.149.9.216"
    assert entry.method == "GET"
    assert entry.path == (
        "/presentations/logstash-monitorama-2013/images/kibana-search.png"
    )
    assert entry.status == 200
    assert entry.size == 203023


def test_parse_line_timestamp_is_parsed_correctly():
    entry = parse_line(VALID_LINE)
    expected = datetime(2015, 5, 17, 10, 5, 3, tzinfo=timezone.utc)
    assert entry.timestamp == expected


def test_parse_line_dash_size_becomes_zero():
    entry = parse_line(VALID_LINE_DASH_SIZE)
    assert entry is not None
    assert entry.size == 0


def test_parse_line_malformed_returns_none():
    assert parse_line(MALFORMED_LINE) is None


def test_parse_line_empty_string_returns_none():
    assert parse_line("") is None


def test_parse_line_bad_date_returns_none():
    assert parse_line(BAD_DATE_LINE) is None


def test_parse_line_bad_status_returns_none():
    assert parse_line(BAD_STATUS_LINE) is None


def test_parse_line_never_raises_on_garbage_input():
    """Parsing garbage must never raise — only return None."""
    garbage_inputs = [
        "\n",
        "   ",
        "not a log line",
        '"""""""',
        "a" * 10_000,  # very long junk line
    ]
    for garbage in garbage_inputs:
        assert parse_line(garbage) is None


# parse_log_file

def test_parse_log_file_valid_lines(tmp_path):
    log_file = tmp_path / "access.log"
    log_file.write_text(VALID_LINE + VALID_LINE_DASH_SIZE)

    results = list(parse_log_file(str(log_file)))

    assert len(results) == 2
    entry1, raw1 = results[0]
    entry2, raw2 = results[1]
    assert entry1 is not None
    assert entry2 is not None
    assert raw1 == VALID_LINE
    assert raw2 == VALID_LINE_DASH_SIZE


def test_parse_log_file_mixed_valid_and_invalid(tmp_path):
    log_file = tmp_path / "access.log"
    log_file.write_text(VALID_LINE + MALFORMED_LINE + VALID_LINE_DASH_SIZE)

    results = list(parse_log_file(str(log_file)))
    entries = [entry for entry, _raw in results]

    assert len(results) == 3
    assert entries[0] is not None
    assert entries[1] is None
    assert entries[2] is not None


def test_parse_log_file_empty_file(tmp_path):
    log_file = tmp_path / "empty.log"
    log_file.write_text("")

    results = list(parse_log_file(str(log_file)))

    assert results == []


def test_parse_log_file_nonexistent_file_raises():
    with pytest.raises(FileNotFoundError):
        list(parse_log_file("/path/does/not/exist.log"))


def test_parse_log_file_is_lazy(tmp_path):
    """Calling parse_log_file should not raise immediately, even for
    a missing file — the error only appears once iteration starts.
    """
    generator = parse_log_file("/path/does/not/exist.log")
    # No exception yet: nothing has been read.
    with pytest.raises(FileNotFoundError):
        next(generator)