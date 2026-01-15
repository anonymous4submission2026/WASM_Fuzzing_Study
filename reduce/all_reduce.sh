# wasm-tools shrink (wasm structure-aware reducer)
find /path/to/__reduction_round2 -type f -name "*.wasm" | xargs -I{} bash -c "bash test_reducer.sh {}"

# lithium (character/line based reducer)
# find /path/to/__reduction_round2 -type f -name "*.wasm" | xargs -I{} bash -c "bash lithium_reducer.sh {}"