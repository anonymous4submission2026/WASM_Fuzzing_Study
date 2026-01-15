#!/bin/bash

get_ref_output() {
  local wasm_path=$1
  local func=$2

  wasm_fname=$(basename $wasm_path)
  wasm_dir=$(dirname "$wasm_path")
  tmp_dir="$wasm_dir/tmp"
  mkdir -p $tmp_dir

  cp $wasm_path $tmp_dir

  bash /path/to/replay_wasm.sh $func $tmp_dir
  python3 /path/to/dedup_output.py $tmp_dir/output

  # Copy the reference deduped output file from tmp/output/deduped to the test case directory
  cp $tmp_dir/output/deduped/*.txt $wasm_dir
  rm -rf $tmp_dir
}

rand() {
  local n=${1:-1}   # default to 1 if no argument given
  for ((i=1; i<=n; i++)); do
    od -An -N4 -tu4 < /dev/urandom | tr -d ' '
  done
}

shrink() {
  local seed=$1
  local wasm_path=$2
  local func=$3

  export WASM_DIR=$(dirname "$wasm_path")
  filename=$(basename $wasm_path .wasm)
  export FILENAME=$filename

  shrunken_wasm_path="$WASM_DIR/shrunken_$FILENAME.wasm"
  shrunken_wat_path="$WASM_DIR/shrunken_$FILENAME.wat"

  export FUNC_NAME=$func
  export TMPDIR="/tmp"

  RUST_LOG=info wasm-tools shrink -a 100000 -s $seed ./reducer_predicate.sh "$wasm_path" -o "$shrunken_wasm_path"
  
  if [ -f "$shrunken_wasm_path" ]; then
    wasm-tools print "$shrunken_wasm_path" -o "$shrunken_wat_path"
  fi

  sleep infinity

  # rm -rf "$WASM_DIR/reduced" 2>/dev/null
}
export -f shrink

# Entry
wasm_path=$1

tc_dir=$(dirname "$wasm_path")
tc_name=$(basename "$wasm_path")
tc_name_with_func=$(basename "$wasm_path" .wasm)
tc="${tc_name_with_func%%__*}"
func="${tc_name_with_func##*__}"

if [ $func == "start" ]; then
  func="_start"
fi

# Create reference output file
get_ref_output $wasm_path $func
if [ ! -f "${tc_dir}/${tc_name_with_func}.txt" ]; then
  echo ""
  echo "ERROR: Reference output file ( ${tc_dir}/${tc_name_with_func}.txt ) was not created. Please check. Stopping reduction."
  exit 1
fi

# Duplicate input test case for each seed and start reducing
mkdir -p "$tc_dir/reductions"

for seed in $(rand 24); do
  echo "Running shrink with seed $seed"

  # Creating duplicate input wasm files and reference output files for each shrink seed
  mkdir -p "$tc_dir/reductions/seed-$seed"
  new_wasm_path="$tc_dir/reductions/seed-$seed/$tc_name"
  cp $wasm_path $new_wasm_path                                        # duplicate of input wasm file
  cp "$tc_dir/$tc_name_with_func.txt" "$tc_dir/reductions/seed-$seed" # duplicate of reference output file

  screen -dmS shrink__seed-${seed} bash -c "shrink $seed $new_wasm_path $func"
done