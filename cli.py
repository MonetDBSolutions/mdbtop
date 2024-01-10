#!/usr/bin/env python3

import sys
import argparse
import curses
import json
from mdbtop import __version__
from mdbtop.monitor import Monitor
from time import sleep
from datetime import datetime, timedelta

PADDING = 4
FIELDS = ['pid', 'pname', 'vms', 'rss', 'cpu_percent', 'database', 'wal', 'bat']
HEADER = ['PID', 'PROC', 'VIRT', 'RSS', 'CPU%', 'DB', 'WAL', 'BAT']
DEFAULT_COL_WIDTHS = [8, 8, 8, 8, 10, 8, 8]


def _convert_bytes_to_human_readable(size_in_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            break
        size_in_bytes /= 1024.0
    return "{:.2f} {}".format(size_in_bytes, unit)


def extract_fields(data, fields):
    res = []
    for proc in data['processes']:
        row = []
        for field in fields:
            value = proc[field]
            #if field in ['vms', 'rss', 'wal', 'bat']:
            #    if type(value) == float or type(value) == int:
            #        value = _convert_bytes_to_human_readable(value)
            row.append(value)
        res.append(row)
    return res


def render(stdscr, data, elapsed):
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    stdscr.addstr(0, 0, f"Time: {elapsed}")
    if data:
        # Calculate column widths
        col_widths = [(max(len(str(item)) for item in col) + PADDING) for col in zip(*data)]
    else:
        col_widths = DEFAULT_COL_WIDTHS
    # draw header
    for i, col_name in enumerate(HEADER):
        stdscr.addstr(1, sum(col_widths[:i]), f"{col_name}")
    if data:
        # draw data
        for i, row in enumerate(data):
            for j, col_width in enumerate(col_widths):
                stdscr.addstr(i + 2, sum(col_widths[:j]), f'{row[j]}')
    stdscr.refresh()


def display_stats(stdscr, log_file, interval):
    start = datetime.now()
    # show header initially 
    render(stdscr, [], timedelta(0))
    with open(log_file) as f:
        while True:
            line = f.readline()
            elapsed = datetime.now() - start
            if line:
                data = extract_fields(json.loads(line), FIELDS)
                render(stdscr, data, elapsed)
            sleep(interval)


def main():
    parser = argparse.ArgumentParser(
        description="Logs system resourse usage for MonetDB processes"
    )
    parser.add_argument(
        "-t",
        "--interval",
        dest="interval",
        type=int,
        default=3,
        action="store",
        help="time interval in seconds"
    )
    parser.add_argument(
        "--log-file",
        dest="log_file",
        type=str,
        action="store",
        help="path to log file"
    )

    parser.add_argument('-v', '--version', action='version', version=f'{__version__}')

    args = parser.parse_args()
    monitor = Monitor(interval=args.interval, log_file=args.log_file)
    monitor.start()
    try:
        curses.wrapper(display_stats, monitor.log, args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        monitor.stop()


if __name__ == "__main__":
    sys.exit(main())
