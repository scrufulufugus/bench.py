#!/usr/bin/env python3

import re
import csv
import sys
import argparse
import subprocess
from time import sleep
from pprint import pprint

TRIALS  = 4
LOG_CNT = 10

def exec(*args):
    print(' '.join(args), file=sys.stderr)
    proc = subprocess.run(args, capture_output=True)
    output = proc.stdout.decode()
    runtime = re.findall(r"^Runtime\s*:\s*(\d*\.?\d*)$", output, re.M)
    try:
        return float(runtime[0])
    except IndexError:
        results = {
            'args'   : proc.args,
            'stdout' : output.split("\n")[-LOG_CNT:],
            'stderr' : proc.stderr.decode().split("\n")[-LOG_CNT:]
        }
        print("Failed: ", end='', file=sys.stderr)
        pprint(results, stream=sys.stderr)
        return float("inf")

def benchmark(input: csv.reader, output: csv.writer, *args):
    for row in input:
        new_args = [ a.format(**row) for a in args ]
        time = float("inf")
        for i in range(TRIALS):
            time = min(time, exec(*new_args))
        row['time'] = time
        writer.writerow(row)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--in", dest='infile', help="Input file",
                        default=sys.stdin, type=argparse.FileType('r'))
    parser.add_argument("-o", "--out", dest='outfile', help="Output file",
                        default=sys.stdout, type=argparse.FileType('w'))
    # TODO: Make -- COMMAND show up in help
    # parser.add_argument("--", dest='command', help="Command",
    #                     type=str, action='extend', required=True)

    try:
        idx = sys.argv.index('--')
    except ValueError:
        parser.print_help()
        parser.exit()
    command = sys.argv[idx+1:]
    sys.argv = sys.argv[:idx]

    args = parser.parse_args()
    reader = csv.DictReader(args.infile)
    writer_fields = reader.fieldnames + ['time']
    writer = csv.DictWriter(args.outfile, writer_fields)
    writer.writeheader()
    benchmark(reader, writer, *command)
    
