#!/usr/bin/env python3

import sys
import os
import argparse
import json
from jinja2 import Environment, FileSystemLoader


def log2list(log_file):
    res = []
    with open(log_file) as f:
        for line in f:
            res.append(json.loads(line))
    return res


def log2html(log_file, out_file=None, header=None):
    data = log2list(log_file)
    templates = os.path.join(os.path.dirname(__file__), 'templates')
    template_env = Environment(loader=FileSystemLoader(templates),
                               keep_trailing_newline=True)
    template = template_env.get_template('index_template.j2')
    js = template_env.get_template('plot.js').render()
    if out_file:
        with open(out_file, 'w') as fout:
            print(template.render(data=json.dumps(data), js=js, header=header), file=fout)
    else:
        print(template.render(data=json.dumps(data), js=js, header=header))


def main():
    parser = argparse.ArgumentParser(
        description="Render mdbtop log to html chart"
    )
    parser.add_argument('log_file')
    parser.add_argument(
        '-o'
        "--out",
        dest="out_file",
        type=str,
        action="store",
        help="path to out_file"
    )
    parser.add_argument(
        "--desc",
        dest="synopsis",
        type=str,
        action="store",
        help="short description to include in the heading"
    )
    args = parser.parse_args()
    return log2html(args.log_file, out_file=args.out_file, header=args.synopsis)


if __name__ == "__main__":
    sys.exit(main())
