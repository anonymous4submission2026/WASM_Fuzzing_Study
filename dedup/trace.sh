#!/bin/bash

# trace_combined.sh: Run LLDB with a custom Python trace_callback for analyzing crashes
#
# Usage:
#   ./trace_combined.sh <program_path> "<program_args>" "<path_filter>" <trace_output_file>
#
# Arguments:
#   program_path       - Path to the target binary
#   program_args       - Quoted string of arguments to pass to the target program
#   path_filter        - Substring to match in file paths to restrict backtrace locations
#   trace_output_file  - File to store backtrace results

# ----------------------------------------------
# Check argument count
# ----------------------------------------------
if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <program_path> \"<program_args>\" \"<path_filter>\" <trace_output_file>"
    echo
    echo "  <program_path>       Path to the target binary"
    echo "  <program_args>       Quoted string of arguments to pass to the target program"
    echo "  <path_filter>        Substring to match in file paths to restrict backtrace locations"
    echo "  <trace_output_file>  File to store backtrace results"
    exit 1
fi

# ----------------------------------------------
# Assign arguments
# ----------------------------------------------
program_path=$1
program_args=$2
path_filter=$3
trace_output_file=$4

# ---------------------------------------------------------------------
# Remove any existing trace output file with the same name
# ---------------------------------------------------------------------
rm $trace_output_file 2&>/dev/null

# ----------------------------------------------
# Run LLDB with inline commands
# ----------------------------------------------
lldb --batch \
    --one-line "script import trace_callback" \
    --one-line "script trace_callback.path_filter = '$path_filter'" \
    --one-line "script trace_callback.trace_output_file = '$trace_output_file'" \
    --one-line "process launch --stop-at-entry" \
    --one-line "process handle SIGSEGV -n true -p true -s true" \
    --one-line "command script add -f trace_callback.crash_hook crash_hook" \
    --one-line "target stop-hook add -o crash_hook" \
    --one-line "process continue" \
    --one-line "quit" \
    -- "$program_path" $program_args
