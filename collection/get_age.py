import subprocess
import json
from datetime import datetime, timezone
import math
import re

TARGET_TO_REPO = {
    "wasmtime": ("bytecodealliance", "wasmtime"),
    "wasmer": ("wasmerio", "wasmer"),
    "wamr": ("bytecodealliance", "wasm-micro-runtime"),
    "wasmedge": ("WasmEdge", "WasmEdge"),
}

def bucket_months(months: float) -> int:
    """Snap a number of months up to the next 12-month block."""
    return math.ceil(months / 12) * 12

def parse_seed(entry: str):
    """
    Parse both formats:
    1. 'seed_wamr_2390.wasm'
    2. 'wasmtime (wasmtime_4669___start)'
    Returns (target, issue_number) or (None, None).
    """
    entry = entry.strip()

    # Format 1: seed_target_issue.wasm
    if entry.startswith("seed_") and entry.endswith(".wasm"):
        try:
            _, target, issue_str = entry.replace(".wasm", "").split("_")
            return target, issue_str
        except ValueError:
            return None, None

    # Format 2: target (target_issue__something)
    m = re.match(r"([a-zA-Z0-9]+)\s*\(\s*([a-zA-Z0-9]+)_(\d+)__", entry)
    if m:
        target_outer = m.group(1)
        target_inner = m.group(2)
        issue_str = m.group(3)
        # sanity check: outer and inner targets should match
        if target_outer != target_inner:
            return None, None
        return target_outer, issue_str

    return None, None

def get_issue_ages(entries):
    results = {}
    now = datetime.now(timezone.utc)
    raw_months = []

    for entry in entries:
        target, issue_str = parse_seed(entry)
        if not target or not issue_str:
            results[entry] = ("[Unrecognized format]", None)
            continue

        repo_info = TARGET_TO_REPO.get(target)
        if not repo_info:
            results[entry] = (f"[Unknown target: {target}]", None)
            continue

        owner, repo = repo_info
        issue_number = issue_str

        try:
            view_cmd = [
                "gh", "issue", "view", issue_number,
                "--repo", f"{owner}/{repo}",
                "--json", "createdAt"
            ]
            output = subprocess.check_output(view_cmd, text=True)
            issue_detail = json.loads(output)
            created_at_str = issue_detail.get("createdAt")
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))

            diff_months = (now - created_at).days / 30.44
            age_months = int(diff_months)
            results[entry] = (created_at_str, age_months)
            raw_months.append(age_months)

        except Exception as e:
            results[entry] = (f"[Error: {e}]", None)

    avg_raw = sum(raw_months) / len(raw_months) if raw_months else 0
    avg_bucketed = bucket_months(avg_raw) if avg_raw > 0 else 0

    return results, avg_raw, avg_bucketed


# Example usage
if __name__ == "__main__":
    entries = "seed_wamr_2397.wasm","seed_wamr_2728.wasm","seed_wamr_2732.wasm","seed_wamr_2847.wasm","seed_wamr_2849.wasm","seed_wamr_3210.wasm","seed_wasmedge_2080.wasm","seed_wasmedge_2748.wasm","seed_wasmedge_3019.wasm","seed_wasmtime_8255.wasm"

    results, avg_raw, avg_bucket = get_issue_ages(entries)
    for entry, (ts, months) in results.items():
        print(f"{entry} → created: {ts}, age: {months} months")

    print(f"\nAverage raw age: {avg_raw:.2f} months")
    print(f"Average age (snapped to next block): {avg_bucket} months")
