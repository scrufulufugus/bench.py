# Bench.py

A simple python script for automating the testing of programs.

## Usage

Below is an example usage of `./bench.py`.

input.csv:

```csv
count
1e2
1e3
1e4
1e5
1e6
1e7
1e8
1e9
```

Call `/bin/time perl -e 'for($i=0;$i<{count};$i++) {}` with `count` from a csv file and record the user time, system time, and CPU percentage.

```sh
./bench.py -i input.csv -o output.csv \
           -r user float '(?P<user>\d*\.?\d*)user' \
           -r system float '(?P<system>\d*\.?\d*)system' \
           -r cpu int '(?P<cpu>\d)%CPU' \
           -- /bin/time perl -e 'for($i=0;$i<{count};$i++) {{}}'
```