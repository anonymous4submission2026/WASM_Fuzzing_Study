#!/usr/bin/env python3
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

# Load CSV file (replace with your file path)
df = pd.read_csv("data.csv")

# Runtimes and seeds
runtimes = ["Wasmtime", "Wasmer", "WAMR", "WasmEdge"]
seeds = ["llvmbench", "rtbench", "wasmbench", "specbench"]
colors = ['tab:blue', 'tab:green', 'tab:orange', 'tab:red']

# Set up 2×2 subplots (no shared axes)
fig, axes = plt.subplots(2, 2, figsize=(10, 8), sharex=False, sharey=False)
axes = axes.flatten()

# Fixed y-axis range and ticks
y_min, y_max = 0, 45
y_ticks = np.arange(y_min, y_max + 1, 5)

for i, runtime in enumerate(runtimes):
    ax = axes[i]
    sub = df[df["runtime"] == runtime]

    if sub.empty:
        ax.text(0.5, 0.5, "No Data", ha="center", va="center", fontsize=10)
        ax.set_title(runtime, fontsize=12)
    else:
        for seed, color in zip(seeds, colors):
            sdata = sub[(sub["seed"] == seed) & (sub["hour"] <= 24)]
            if not sdata.empty:
                ax.plot(
                    sdata["hour"], sdata["coverage"],
                    marker='o', color=color, label=seed
                )

        ax.set_title(runtime, fontsize=14)
        ax.set_xlabel("Time (hours)")
        ax.set_ylabel("Cumulative Coverage (%)")

    # Apply fixed axis limits and tick labels
    ax.set_ylim(y_min, y_max)
    ax.set_yticks(y_ticks)
    ax.set_yticklabels([f"{v}%" for v in y_ticks])

    # X-axis ticks every 4 hours
    x_max = max(sub["hour"]) if not sub.empty else 24
    ax.set_xticks(np.arange(0, x_max + 4, 4))
    ax.set_xticklabels([f"{v}h" for v in np.arange(0, x_max + 4, 4)])

    ax.grid(True, linestyle='--', alpha=0.5)
    ax.tick_params(axis='both', labelsize=12, labelbottom=True, labelleft=True)

# Force all subplots to display their tick labels
for ax in axes:
    ax.tick_params(labelbottom=True, labelleft=True)

# Shared legend and layout
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, -0.025), ncol=4, fontsize=15, frameon=False)
fig.tight_layout(rect=[0, 0.05, 1, 1])

plt.savefig("coverage_progress.pdf", dpi=300, bbox_inches="tight")
plt.close(fig)
