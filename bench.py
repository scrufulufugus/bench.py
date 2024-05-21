#!/usr/bin/env python3

import re
import csv
import sys
import argparse
import subprocess
from itertools import product
from time import sleep # TODO: Configurable sleep between runs
from pydoc import locate
from pprint import pprint
from typing import Iterable, TextIO

TRIALS  = 4 # TODO: Make this an argument
LOG_CNT = 10

class Benchmark(object):
    """
    Benchmark class
    """
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
            m = re.search(val['pattern'], output)
            if m:
                results[key] = val['type'](m.group(key))
            else:
                results = {
                    'args'   : proc.args,
                    'output' : output.split("\n")[-LOG_CNT:],
                }
                print("Failed: ", end='', file=sys.stderr)
                pprint(results, stream=sys.stderr)
                return None
        return results

    def run(self, input: Iterable[str], output: TextIO):
        reader = csv.DictReader(input)
        writer_fields = reader.fieldnames + [ key for key in self.records ]
        writer = csv.DictWriter(output, writer_fields)
        writer.writeheader()

        for row in reader:
            new_args = [ a.format(**row) for a in self.args ]
            best = None
            for i in range(TRIALS):
                results = self.exec(new_args)

                # Skip failed runs
                if results == None:
                    continue

                # TODO: Customize order_by operator
                if best == None or results[self.order_by] < best[self.order_by]:
                    best = results

            # Write best result
            if best != None:
                row.update(best)
                writer.writerow(row)
                output.flush() # Write lines immediately so we can ^C

def mutli_input_cross(*files):
    """
    Cross product of multiple input files
    """
    header = [ f.readline().rstrip() for f in files ]
    yield ','.join(header) + '\n'

    cross = product(*files)
    for line in cross:
        yield ','.join([ l.rstrip() for l in line ]) + '\n'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--in", dest='infile', help="Input file", action='append',
                        type=argparse.FileType('r'), required=False)
    parser.add_argument("-o", "--out", dest='outfile', help="Output file",
                        default=sys.stdout, type=argparse.FileType('w'))
    parser.add_argument("-r", "--record", dest='records',
                        help="Stores a value matching the second argument into a column matching the first",
                        action='append', nargs=3, required=True)
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

    # If we have mutliple input files
    # we want a cross product of their lines
    if args.infile == None:
        infile = sys.stdin
    elif len(args.infile) == 1:
        infile = args.infile[0]
    else:
        infile = mutli_input_cross(*args.infile)

    # Define output format
    outputs = {}
    for record in args.records:
        if record[0] in outputs:
            print("Duplicate key", record[0], file=sys.stderr)
            sys.exit(2)
        pattern = re.compile(record[2], re.M)
        if record[0] not in pattern.groupindex:
            print("Pattern", pattern.pattern, "is missing group", record[0])
            sys.exit(2)
        outputs[record[0]] = {
            'pattern' : pattern,
            'type' : locate(record[1])
        }

    # Create benchmark
    benchmark = Benchmark(outputs, command)
    
    # Run benchmark
    benchmark.run(infile, args.outfile)

    # Close files
    if args.infile != None:
        for f in args.infile:
            f.close()
    args.outfile.close()