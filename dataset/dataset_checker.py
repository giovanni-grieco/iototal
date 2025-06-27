import sys
import os

allgood_flag = True

for line in sys.stdin:
    cols = line.split(',')
    #print(len(cols))
    if len(cols) != 40:
        allgood_flag = False
        print(f"Error: Expected at least 40 columns, found {len(cols)} in line: {line.strip()}")

if allgood_flag:
    print("No errors found, all good!")
    print("All lines have the expected number of columns (40).")
