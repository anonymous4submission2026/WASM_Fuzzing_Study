# WASM Fuzzing Study Artifacts

This is an artifact repository for the paper **"Left Behind, Not Forgotten: Reusing Regression Tests to Find Bugs in WebAssembly Runtimes"**.

The paper reports on a large-scale study assessing the benefits of reusing regression tests to find bugs in WebAssembly runtimes. The study explores two scenarios: (1) **transplanting** regression tests across runtimes to find runtime-specific bugs, and (2) using regression tests as **seed corpora for fuzzing campaigns**.

The mined seed corpus `rtbench` (*Regression Test Bench*) is available in this repository's release artifacts: [rtbench.tar.gz](https://github.com/anonymous4submission2026/WASM_Fuzzing_Study/releases/download/v0.0.1/rtbench.tar.gz).

---

## Repository Structure

```
collection/     # Mine regression tests from WASM runtime GitHub issues
exec_oracle/    # Execute tests across runtimes and normalize outputs
dedup/          # LLDB-based crash tracing and differential analysis
reduce/         # Minimize failing test cases to smallest reproducers
measure/        # File size and structural complexity statistics
plots/          # Publication figures for each research question (RQ1–RQ5)
```

---

## Prerequisites

**WASM Runtimes** (all four must be on `PATH`):
- [Wasmtime](https://wasmtime.dev/)
- [Wasmer](https://wasmer.io/)
- [WAMR / iwasm](https://github.com/bytecodealliance/wasm-micro-runtime) — includes `wamrc` AOT compiler
- [WasmEdge](https://wasmedge.org/)

**Tooling:**
- [`wasm-tools`](https://github.com/bytecodealliance/wasm-tools) — structure-aware WASM shrink
- [`wasm-objdump`](https://github.com/WebAssembly/wabt) (WABT) — disassembly for nesting-depth measurement
- [`gh`](https://cli.github.com/) CLI — authenticated, for issue mining
- `lldb` with Python API — crash tracing
- GNU `screen` — parallel reduction sessions

**Python 3** with packages: `pandas`, `matplotlib`, `plotly`, `seaborn`, `requests`

---

## Pipeline

### 1. Collection — Mine regression tests from GitHub

```bash
python3 collection/collect_issues.py <owner> <repo> <limit> <storage_dir>
python3 collection/process_issues.py <issues_directory>
```

`collect_issues.py` fetches bug-labeled issues and comments from a WASM runtime repository using the `gh` CLI. `process_issues.py` filters them by bug-related keywords, extracts embedded code blocks and linked `.wasm`/`.wat` files, and saves one directory per issue.

### 2. Execution Oracle — Run tests across all runtimes

```bash
bash exec_oracle/replay_wasm.sh <function_name> <wasm_directory>
python3 exec_oracle/dedup_output.py <output_directory>
```

`replay_wasm.sh` executes each WASM file on all four runtimes (with multiple backends each) and writes normalized outputs to `{filename}__{function}.txt`. Each line is tagged:

```
wasmtime:<>:out_of_bounds
wasmer_cranelift:<>:num#
```

Runtime-specific error messages (stack overflow, out-of-bounds, type mismatch, etc.) and numeric outputs are normalized so results are comparable across runtimes. `dedup_output.py` deduplicates the collected outputs.

| Runtime | Backends |
|---------|----------|
| Wasmtime | Winch, Cranelift |
| Wasmer | Cranelift, LLVM |
| WAMR / iwasm | AOT, LLVM-JIT |
| WasmEdge | JIT, AOT, Interpreter |

### 3. Test Reduction — Minimize failing test cases

```bash
# Structure-aware reduction (24 parallel seeds via GNU screen)
bash reduce/test_reducer.sh <wasm_path>

# Character/line-level reduction via Lithium
bash reduce/lithium_reducer.sh <wasm_path>

# Batch reduction over a directory
bash reduce/all_reduce.sh
```

> **Before running:** update the hardcoded paths in `reduce/test_reducer.sh`, `reduce/lithium_reducer.sh`, and `reduce/lithium_predicate.py` to point to your local `replay_wasm.sh` and `dedup_output.py`.

A candidate reduction is considered "interesting" if its normalized oracle output matches the original's, ensuring the reduced file still triggers the same behavior.

### 4. Measurement

```bash
python3 measure/measure_file_stats.py <directory>
bash measure/measure_avg_nesting_depths.sh <directory>
```

Computes file size statistics (count, min, max, mean, median, stddev) and average WASM block/loop/if nesting depth using `wasm-objdump`.

### 5. Plots — Reproduce paper figures

Each research question has its own subdirectory under `plots/`:

| Script | Figure |
|--------|--------|
| `plots/rq1/transplantation_timeline/main4.py` | Bug reveal vs. report timeline across runtime pairs |
| `plots/rq1/transplantation_heatmap/transplantation.py` | Cross-runtime transplantation heatmap |
| `plots/rq2/venn/seedbugs.py` | Venn diagram: bug overlap across seed corpora |
| `plots/rq2/coverage_progress/progress.py` | Cumulative bug coverage curves per runtime |
| `plots/rq5/lineage_sankey/lineage.py` | Sankey diagram of regression lineage by seed age |

Run any script from its own directory (`cd plots/rqN/... && python3 <script>.py`). Input data (`.csv`, `.tsv`, `.txt`) lives alongside each script.

---

## Key Data Files

| File | Description |
|------|-------------|
| `plots/rq1/transplantation_timeline/bug.csv` | Per-bug reveal/report runtime and dates |
| `plots/rq5/data/lineage_diagram.tsv` | Seed → bug → runtime lineage relationships |
| `plots/rq2/venn/*.txt` | Bug ID lists for rtbench, llvmbench, wasmbench, specbench |
| `plots/rq3/WASM_Fuzzing_Study_Bugs.csv` | Full bug classification used in RQ3 and RQ4 |
