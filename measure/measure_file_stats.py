#!/usr/bin/env python3
import os
import sys
import statistics

def main(directory):
    if not os.path.isdir(directory):
        print(f"Usage: {sys.argv[0]} <directory>")
        sys.exit(1)

    sizes = []
    for root, _, files in os.walk(directory):
        for f in files:
            path = os.path.join(root, f)
            try:
                sizes.append(os.path.getsize(path))
            except Exception as e:
                print(f"Warning: could not read {path}: {e}")

    if not sizes:
        print("No files found.")
        return

    sizes.sort()
    n = len(sizes)
    print(f"Count: {n}")
    print(f"Min: {min(sizes)} bytes")
    print(f"Max: {max(sizes)} bytes")
    print(f"Mean: {statistics.fmean(sizes):.2f} bytes")
    print(f"Median: {statistics.median(sizes):.2f} bytes")
    print(f"SD: {statistics.pstdev(sizes):.2f} bytes")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <directory>")
        sys.exit(1)
    main(sys.argv[1])

