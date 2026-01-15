import os
import shutil
import subprocess

def interesting(args, prefix):
    """
    Lithium interestingness test.
    Returns True if the reduced testcase is still interesting
    (i.e., new output matches reference output), else False.
    """

    if not args:
        print("[!] No input file provided to interesting()")
        return False

    temp_wasm_path = args[-1]

    # Required environment variables
    WASM_DIR = os.environ.get("WASM_DIR")
    FUNC_NAME = os.environ.get("FUNC_NAME")
    FILENAME = os.environ.get("FILENAME")

    if not (WASM_DIR and FUNC_NAME and FILENAME):
        print("[!] Missing environment variables: WASM_DIR, FUNC_NAME, FILENAME")
        return False

    reduced_dir = os.path.join(WASM_DIR, "reduced")
    os.makedirs(reduced_dir, exist_ok=True)

    # Copy candidate to reduced directory
    temp_copy = os.path.join(reduced_dir, f"temp__{FUNC_NAME}.wasm")
    shutil.copy(temp_wasm_path, temp_copy)

    ref_output_path = os.path.join(WASM_DIR, f"{FILENAME}.txt")
    new_output_dir = os.path.join(reduced_dir, "output")
    new_dedup_dir = os.path.join(new_output_dir, "deduped")
    new_output_path = os.path.join(new_dedup_dir, f"temp__{FUNC_NAME}.txt")

    # Run replay and dedup
    subprocess.run(
        ["/bin/bash", "/path/to/replay_wasm.sh", FUNC_NAME, reduced_dir],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    subprocess.run(
        ["python3", "/path/to/dedup_output.py", new_output_dir],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Read reference and new outputs as strings
    ref_content = ""
    new_content = ""

    if os.path.exists(ref_output_path):
        with open(ref_output_path, "r", errors="ignore") as f:
            ref_content = f.read().strip()

    if os.path.exists(new_output_path):
        with open(new_output_path, "r", errors="ignore") as f:
            new_content = f.read().strip()

    # Print logs similar to the bash version
    print("++++++++++++++++++++++++++++++++++++++++++")
    print(f"REF: {ref_output_path}")
    print(ref_content)
    print("++++++++++++++++++++++++++++++++++++++++++")
    print(f"NEW: {new_output_path}")
    print(new_content)
    print("++++++++++++++++++++++++++++++++++++++++++")

    # Compare contents
    if ref_content == new_content:
        print("DIFF: identical")
        interesting_result = True
    else:
        print("DIFF: contents differ")
        interesting_result = False

    print("++++++++++++++++++++++++++++++++++++++++++")

    # Clean up
    cleanup_paths = [
        os.path.join(new_output_dir, f"temp__{FUNC_NAME}__{FUNC_NAME}.txt"),
        new_output_path,
        temp_copy,
    ]
    for path in cleanup_paths:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass

    return interesting_result
