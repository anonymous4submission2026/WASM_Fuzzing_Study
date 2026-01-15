import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Load TSV
df = pd.read_csv("../data/lineage_diagram.tsv", sep="\t")

# Normalize runtime names (capitalize consistently)
runtime_map = {
    "wasmtime": "Wasmtime",
    "wasmer": "Wasmer",
    "wamr": "WAMR",
    "wasmedge": "WasmEdge"
}
df["seed_runtime"] = df["seed_runtime"].map(runtime_map)
df["buggy_runtime"] = df["buggy_runtime"].map(runtime_map)

# Filter transplantation rows only
df_t = df[df["mode"] == "transplantation"]

# Runtimes in fixed order
runtimes = ["Wasmtime", "Wasmer", "WAMR", "WasmEdge"]

# Initialize count matrix
bug_counts = np.full((len(runtimes), len(runtimes)), np.nan)

# Count occurrences
for i, origin in enumerate(runtimes):
    for j, target in enumerate(runtimes):
        if origin != target:
            count = ((df_t["seed_runtime"] == origin) &
                     (df_t["buggy_runtime"] == target)).sum()
            bug_counts[i, j] = count

# Annotation labels: numbers or "-" on diagonal
annot_labels = [[
    "-" if i == j else str(int(bug_counts[i, j]))
    for j in range(len(runtimes))
] for i in range(len(runtimes))]

# Plot heatmap
plt.figure(figsize=(6, 5))
ax = sns.heatmap(
    bug_counts,
    annot=annot_labels, fmt="",
    cmap="viridis", cbar=True,
    xticklabels=runtimes,
    yticklabels=runtimes,
    mask=np.isnan(bug_counts),
    annot_kws={"fontsize": 15, "fontweight": "bold"}
)

ax.set_xlabel("Target Runtime", fontsize=15, fontweight="bold")
ax.set_ylabel("Origin Runtime", fontsize=15, fontweight="bold")
ax.set_title("", fontsize=15, fontweight="bold")

ax.set_xticklabels(ax.get_xticklabels(), fontsize=12, rotation=0)
ax.set_yticklabels(ax.get_yticklabels(), fontsize=12, rotation=0)

plt.tight_layout()
plt.savefig("transplantation_heatmap.pdf", dpi=300, bbox_inches="tight")
