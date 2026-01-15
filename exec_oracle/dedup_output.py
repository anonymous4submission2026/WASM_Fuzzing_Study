#!/usr/bin/python3

import os
import sys
import re
from pathlib import Path

MIN_INPUT_LINES = 10
to_remove = []

unique_output_diffs = {}

def normalize_numeric_outputs(line, output_map, counter):
  # Normalize only if line has ':<>:'
  if ":<>:" not in line:
      return line, counter

  prefix, output = line.split(":<>:", 1)
  output = output.strip()

  if "panic" in output and "enums.rs" in output:
    if "load double" in output:
      normalized_output = "panic_enums_load_double"
    else:
      normalized_output = "panic"
  elif "Unable to compile" in output:
    normalized_output = "compilation_error"
  elif "LLVM ERROR" in output:
    normalized_output = "llvm_error"
  elif "No such file" in output:
    normalized_output = "file_not_found"
  elif "validation failed" in output or "Invalid" in output or "does not support" in output:
    normalized_output = "invalid"
  elif "table grow" in output:
    normalized_output = "table_grow_error"
  elif "undefined_element" in output:
    normalized_output = "out_of_bounds"
  elif "call stack exhausted" in output or "calling stack exhausted" in output:
    normalized_output = "stack_overflow"
  elif "Pointer not aligned" in output:
    normalized_output = "unaligned_pointer"
  elif "unreachable" in output:
    normalized_output = "unreachable"
  elif "no func export" in output or "lookup function" in output or "export a function" in output or "wasm function not found" in output:
    normalized_output = "no_func"
  elif "out of bounds" in output:
    normalized_output = "out_of_bounds"
  elif "failed to invoke" in output:
    normalized_output = "invocation_error"
  elif "[error] calling stack" in output:
    normalized_output = "[error] calling stack"
  elif "integer divide by zero" in output:
    normalized_output = "integer_divide_by_zero"
  elif "does not support" in output:
    normalized_output = "unsupported"
  else:
    # Match outputs that consist of only numbers and whitespace
    if all(re.fullmatch(r'(?i)(-?\d+(\.\d+)?|-?inf|-?nan)', token) for token in output.split()):
      if output not in output_map:
        output_map[output] = f"num{counter}"
        counter += 1
      normalized_output = output_map[output]
    else:
      normalized_output = output

  return f"{prefix}:<>:{normalized_output}", counter

def build_normalized_output_to_test_id_map(file_name, lines):
  global unique_output_diffs

  current_block = []
  current_test_id = None

  number_map = {}
  num_counter = 1

  for line in lines:
    line = line.strip()

    if "DIFF" in line:
        continue

    if current_test_id is None:
      current_test_id = file_name
    normalized_line, num_counter = normalize_numeric_outputs(line, number_map, num_counter)
    current_block.append(normalized_line)

  if current_block:
    block_str = "\n".join(current_block).strip()
    unique_output_diffs[block_str] = current_test_id

if __name__ == "__main__":
  output_dir = Path(sys.argv[1])
  deduped_dir = output_dir / "deduped"
  Path(deduped_dir).mkdir(parents=True, exist_ok=True)

  for file in output_dir.glob("*.txt"):
    with open(file, 'r', encoding="ISO-8859-1") as output_file:
      input_lines = output_file.readlines()
      # print(input_lines)

      if len(input_lines) < MIN_INPUT_LINES:
        to_remove.append(file)
      else:
        # Deduplicated mapping using normalization
        build_normalized_output_to_test_id_map(file.name, input_lines)

  # Print normalized deduped blocks
  for (outputs, file_name) in unique_output_diffs.items():
    with open(deduped_dir / f"{file_name}.txt", "w+") as deduped_output_file:
      deduped_output_file.write(outputs + "\n")

  # Remove incomplete files
  for file in to_remove:
    os.remove(file)
      
