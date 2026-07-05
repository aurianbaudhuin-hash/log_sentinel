"""Tests for logsentinel.cli."""

import json
import csv
from datetime import timezone

import pytest

from logsentinel.cli import parse_args, _parse_date_arg, export_json, export_csv
from logsentinel.stats import Report


# parse_args

def test_parse_args_defaults():
    args = parse_args(["logs.txt"])
    assert args.logfile == "logs.txt"
    assert args.top == 10
    assert args.export is None


def test_parse_args_custom_top_and_export():
    args = parse_args(["logs.txt", "--top", "5", "--export", "json"])
    assert args.top == 5
    assert args.export == "json"


def test_parse_args_invalid_export_choice_exits():
    with pytest.raises(SystemExit):
        parse_args(["logs.txt", "--export", "xml"])


# _parse_date_arg

def test_parse_date_arg_none_returns_none():
    assert _parse_date_arg(None, "--from") is None


def test_parse_date_arg_valid_format():
    result = _parse_date_arg("01/Jan/2026", "--from")
    assert result.year == 2026
    assert result.month == 1
    assert result.day == 1
    assert result.tzinfo == timezone.utc


def test_parse_date_arg_invalid_format_exits():
    with pytest.raises(SystemExit):
        _parse_date_arg("not-a-date", "--from")


# export_json / export_csv

def make_test_report():
    return Report(
        valid_count=10,
        ignored_count=2,
        status_code_count={200: 8, 404: 2},
        hour_counter={10: 5, 14: 5},
        error_ips={"1.1.1.1": 2},
        average_size=512.5,
        top_ips=["1.1.1.1", "2.2.2.2"],
    )


def test_export_json_writes_expected_fields(tmp_path):
    report = make_test_report()
    filepath = tmp_path / "report.json"

    export_json(report, str(filepath))

    with open(filepath) as f:
        data = json.load(f)

    assert data["valid_count"] == 10
    assert data["ignored_count"] == 2
    assert data["top_ips"] == ["1.1.1.1", "2.2.2.2"]


def test_export_csv_writes_header(tmp_path):
    report = make_test_report()
    filepath = tmp_path / "report.csv"

    export_csv(report, str(filepath))

    with open(filepath, newline="") as f:
        rows = list(csv.reader(f))

    assert rows[0] == ["Metric", "Value"]