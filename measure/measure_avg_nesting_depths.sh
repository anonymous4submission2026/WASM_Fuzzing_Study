#!/bin/bash

# Script to analyze average nesting depth of WebAssembly files
# Usage: ./analyze_wasm_depth.sh <directory_path>

set -e

# Check if directory argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <directory_path>"
    echo "Analyzes nesting depth of .wasm files in the specified directory"
    exit 1
fi

DIR="$1"

# Check if directory exists
if [ ! -d "$DIR" ]; then
    echo "Error: Directory '$DIR' does not exist"
    exit 1
fi

# Check if wasm-objdump is available
if ! command -v wasm-objdump &> /dev/null; then
    echo "Error: wasm-objdump not found. Please install WABT (WebAssembly Binary Toolkit)"
    echo "Install with: apt-get install wabt (Ubuntu/Debian) or brew install wabt (macOS)"
    exit 1
fi

# Array to store average depths for each file
depths=()

echo "Analyzing .wasm files in: $DIR"
echo "----------------------------------------"

# Find all .wasm files and process them
while IFS= read -r -d '' wasm_file; do
    filename=$(basename "$wasm_file")
    
    # Use wasm-objdump to analyze the file and calculate nesting depth
    # The -d flag disassembles, we look for block/loop/if nesting
    depth=$(wasm-objdump -d "$wasm_file" 2>/dev/null | \
        awk '
        BEGIN { max_depth = 0; depth = 0 }
        /block|loop|if/ { depth++; if (depth > max_depth) max_depth = depth }
        /end/ { if (depth > 0) depth-- }
        END { print max_depth }
        ')
    
    if [ -n "$depth" ]; then
        echo "$filename: avg nesting depth = $depth"
        depths+=("$depth")
    fi
done < <(find "$DIR" -maxdepth 1 -type f -name "*.wasm" -print0)

# Check if any .wasm files were found
if [ ${#depths[@]} -eq 0 ]; then
    echo "No .wasm files found in directory"
    exit 0
fi

echo "----------------------------------------"

# Calculate overall average
sum=0
for d in "${depths[@]}"; do
    sum=$(echo "$sum + $d" | bc)
done
avg=$(echo "scale=2; $sum / ${#depths[@]}" | bc)

# Calculate standard deviation
sum_sq_diff=0
for d in "${depths[@]}"; do
    diff=$(echo "$d - $avg" | bc)
    sq_diff=$(echo "$diff * $diff" | bc)
    sum_sq_diff=$(echo "$sum_sq_diff + $sq_diff" | bc)
done
variance=$(echo "scale=2; $sum_sq_diff / ${#depths[@]}" | bc)
stddev=$(echo "scale=2; sqrt($variance)" | bc)

# Display results
echo "Number of .wasm files analyzed: ${#depths[@]}"
echo "Overall average nesting depth: $avg"
echo "Standard deviation: $stddev"
