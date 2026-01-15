#!/bin/bash

# The input wasm_path should be the path to a temporary wasm_path which is ideally copied from the original directory into a reduced directory
temp_wasm_path=$1

reduced_dir="$WASM_DIR/reduced"
mkdir -p $reduced_dir
cp $temp_wasm_path $reduced_dir/temp__${FUNC_NAME}.wasm

ref_output_path="$WASM_DIR/${FILENAME}.txt"
new_output_path="$reduced_dir/output/deduped/temp__${FUNC_NAME}.txt"

bash /path/to/replay_wasm.sh $FUNC_NAME "$reduced_dir"
python3 /path/to/dedup_output.py "$reduced_dir/output"

diff_output=$(diff "$ref_output_path" "$new_output_path")
diff_status=$?

echo "++++++++++++++++++++++++++++++++++++++++++"
echo "REF: $ref_output_path"
cat "$ref_output_path"
echo "++++++++++++++++++++++++++++++++++++++++++"
echo "NEW: $new_output_path"
cat "$new_output_path"
echo "++++++++++++++++++++++++++++++++++++++++++"
echo "DIFF:"
echo "$diff_output"
echo "++++++++++++++++++++++++++++++++++++++++++"

rm "$reduced_dir/output/temp__${FUNC_NAME}__${FUNC_NAME}.txt"
rm "$reduced_dir/output/deduped/temp__${FUNC_NAME}.txt"
rm "$reduced_dir/temp__${FUNC_NAME}.wasm"

if [ "$diff_status" -eq 0 ]; then
  exit 0
else
  exit 1
fi