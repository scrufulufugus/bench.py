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

class Benchmark(object):
    def __init__(self, records: dict[str, dict], args: tuple[str]):
        self.records = records
        self.args = args
        self.order_by = next(iter(records))

    def exec(self, args):
        print(' '.join(args), file=sys.stderr)
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = proc.stdout.decode()
        results = {}
        for key, val in self.records.items():
            m = re.search(val, output)
            if m:
                results[key] = float(m.group(key))
            else:
                results = {
                    'args'   : proc.args,
                    'output' : output.split("\n")[-LOG_CNT:],
                }
                print("Failed: ", end='', file=sys.stderr)
                pprint(results, stream=sys.stderr)
                return None
        return results

    def run(self, input: csv.reader, output: csv.writer):
        for row in input:
            new_args = [ a.format(**row) for a in self.args ]
            best = { rec : float("inf") for rec in self.records }
            for i in range(TRIALS):
                results = self.exec(new_args)
                if results[self.order_by] < best[self.order_by]:
                    best = results
            row.update(best)
            writer.writerow(row)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--in", dest='infile', help="Input file",
                        default=sys.stdin, type=argparse.FileType('r'))
    parser.add_argument("-o", "--out", dest='outfile', help="Output file",
                        default=sys.stdout, type=argparse.FileType('w'))
    parser.add_argument("-r", "--record", dest='records',
                        help="Stores a value matching the second argument into a column matching the first",
                        action='append', nargs=2, required=True)
    # TODO: Make -- COMMAND show up in help
    # parser.add_argument("--", dest='command', help="Command",
    #                     type=str, action='extend', required=True)

    # Parse command string
    try:
        idx = sys.argv.index('--')
    except ValueError:
        parser.print_help()
        parser.exit()
    command = sys.argv[idx+1:]
    sys.argv = sys.argv[:idx]

    args = parser.parse_args()

    # Define output format
    outputs = {}
    for record in args.records:
        if record[0] in outputs:
            print("Duplicate key", record[0], file=sys.stderr)
            sys.exit(2)
        pattern = re.compile(record[1], re.M)
        if record[0] not in pattern.groupindex:
            print("Pattern", pattern.pattern, "is missing group", record[0])
            sys.exit(2)
        outputs[record[0]] = pattern

    benchmark = Benchmark(outputs, command)
    
    # Open input and output
    reader = csv.DictReader(args.infile)
    writer_fields = reader.fieldnames + [ key for key in outputs ]
    writer = csv.DictWriter(args.outfile, writer_fields)
    writer.writeheader()
    
    benchmark.run(reader, writer)
    
