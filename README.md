# logsentinel

**logsentinel** is a fast, dependency-free command-line tool for analyzing Apache "combined log" files. It was built to give teams a self-contained way to extract insights from web server logs without relying on paid third-party software.

## Features

- **Top N IP addresses** by request count (N configurable, default 10)
- **Hourly request distribution** (0–23h)
- **HTTP status code breakdown** (200, 404, 500, etc.)
- **Average response size**, in bytes
- **Error tracking**: IP addresses that generated at least one 4xx/5xx response
- **Date range filtering** via `--from` and `--to`
- **Export** to JSON or CSV
- **Fault-tolerant parsing**: malformed lines are skipped and counted, never crash the program
- Reliable on large files thanks to a streaming, line-by-line architecture

## Requirements

- Python 3.11+
- No third-party dependencies for the core program (standard library only)

## Installation

Clone the repository and run it directly with Python — no installation step is required for the core tool.

```bash
git clone https://github.com/aurianbaudhuin-hash/logsentinel.git
cd logsentinel
```

For running the test suite, install the development dependencies:

```bash
pip install -r requirements-dev.txt
```

## Usage

```bash
python -m logsentinel.cli <logfile_path> [options]
```

### Options

| Flag | Description | Default |
|---|---|---|
| `--top N` | Number of top IPs to display | `10` |
| `--export {json,csv}` | Export the report to JSON or CSV | none (terminal only) |
| `--output PATH` | Destination file for the export | `static/report.json` / `static/report.csv` |
| `--from DD/Mon/YYYY` | Only include entries on or after this date | none |
| `--to DD/Mon/YYYY` | Only include entries on or before this date | none |

### Examples

Analyze a log file and print a report to the terminal:

```bash
python -m logsentinel.cli access.log
```

Show the top 5 IPs and export the report as JSON:

```bash
python -m logsentinel.cli access.log --top 5 --export json --output report.json
```

Filter by date range:

```bash
python -m logsentinel.cli access.log --from 01/Jan/2026 --to 31/Jan/2026
```

## Expected log format

logsentinel parses the Apache **combined log** format:

```
IP - - [DD/Mon/YYYY:HH:MM:SS +0000] "METHOD /path HTTP/1.1" STATUS SIZE
```

Example:

```
83.149.9.216 - - [17/May/2015:10:05:03 +0000] "GET /index.html HTTP/1.1" 200 203023
```

Any line that doesn't match this format — or that has an unparseable date — is skipped and counted separately. logsentinel never crashes on malformed input; it reports how many lines were valid and how many were ignored at the end of the run.

## Project structure

```
logsentinel/
├── logsentinel/
│   ├── __init__.py
│   ├── parser.py      # line-by-line log extraction (regex-based)
│   ├── stats.py        # aggregation, sorting, and report generation
│   └── cli.py           # argparse-based command-line interface
├── tests/
│   ├── test_parser.py
│   ├── test_stats.py
│   └── test_cli.py
├── generate_fake_logs.py   # generates realistic fake log files for testing
├── requirements-dev.txt
├── pyproject.toml
└── README.md
```

### Architecture overview

- **`parser.py`** is a pure, self-contained module. It exposes a generator, `parse_log_file()`, that reads a log file lazily — one line at a time — so memory usage stays constant regardless of file size. Each line is parsed independently by `parse_line()`, which returns either a `LogEntry` or `None` if the line is malformed. This module never raises exceptions for bad input; a malformed line is treated as an expected case, not a fatal error.
- **`stats.py`** consumes the stream produced by `parser.py` and builds a `Report`: request counts by IP, hour, and status code, average response size, and the list of IPs responsible for errors. It also implements a custom sorting algorithm (see below) to rank IPs by request count.
- **`cli.py`** is the only module that touches `argparse`, the terminal, and the filesystem for exports. It orchestrates the other two modules and translates their output into a readable table or a JSON/CSV file.

This separation means `parser.py` and `stats.py` can be reused independently of the command-line interface — for example, in a future web dashboard — without modification.

## Testing

The project has a pytest suite covering the parser, statistics engine, and CLI, including:

- valid and malformed log lines
- edge cases (empty size field, unparseable dates, missing files)
- Top N ranking correctness
- JSON and CSV export
- date range filtering
- empty file handling

Run the full test suite:

```bash
pytest tests/ -v
```

## Code quality

The codebase is formatted with **black** and linted with **ruff** (or flake8). Tooling is listed in `requirements-dev.txt`.

```bash
black logsentinel/ tests/ generate_fake_logs.py
ruff check logsentinel/ tests/ generate_fake_logs.py
```

## Generating test data

`generate_fake_logs.py` produces a plausible fake log file, including a configurable proportion of intentionally malformed lines, useful for both unit testing and performance benchmarking.

```bash
python generate_fake_logs.py --count 50000 --output static/fake_logs.txt --malformed-ratio 0.02
```

| Flag | Description | Default |
|---|---|---|
| `--count` | Number of lines to generate | `50000` |
| `--output` | Destination file path | `static/fake_logs.txt` |
| `--malformed-ratio` | Fraction of intentionally malformed lines | `0.02` |

## Roadmap / possible extensions

- Suspicious pattern detection (e.g. more than 100 requests/minute from a single IP, flagged as a potential scan)
- ASCII bar chart of the hourly request distribution directly in the terminal

## Technologies used

- **Python 3.11+** — core language, standard library only for the main program
- **`re`** — log line parsing via regular expressions
- **`argparse`** — command-line interface
- **`dataclasses`** — typed data structures (`LogEntry`, `Report`)
- **`collections` / plain dicts** — aggregation and counting
- **`json`** / **`csv`** — report export
- **`pytest`** — test suite
- **`black`** / **`ruff`** — code formatting and linting
