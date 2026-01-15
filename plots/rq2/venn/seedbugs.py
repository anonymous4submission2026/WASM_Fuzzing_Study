#!/usr/bin/env python3
import matplotlib.pyplot as plt
from venn import venn
from matplotlib.patches import Patch

def read_list_from_file(filename):
    """Read non-empty, stripped lines from a text file into a set."""
    with open(filename, "r") as f:
        return {line.strip() for line in f if line.strip()}

def main():
    # Read sets from files
    llvmbench = read_list_from_file("llvmbench.txt")
    rtbench = read_list_from_file("rtbench.txt")
    wasmbench = read_list_from_file("wasmbench.txt")
    specbench = read_list_from_file("specbench.txt")

    # Create labeled names with counts
    names = {
        "llvmbench": f"llvmbench ({len(llvmbench)})",
        "rtbench": f"rtbench ({len(rtbench)})",
        "wasmbench": f"wasmbench ({len(wasmbench)})",
        "specbench": f"specbench ({len(specbench)})"
    }

    # Combine into dict for venn()
    data = {
        names["llvmbench"]: llvmbench,
        names["rtbench"]: rtbench,
        names["wasmbench"]: wasmbench,
        names["specbench"]: specbench
    }

    # Use a color-blind–friendly palette (Okabe–Ito)
    colorblind_palette = [
        "#0072B2",  # blue
        "#E69F00",  # orange
        "#009E73",  # green
        "#D55E00"   # red
    ]

    # Plot the Venn diagram
    fig, ax = plt.subplots(figsize=(7, 7))
    v = venn(data, ax=ax, cmap=colorblind_palette)

    # Increase font sizes and move labels up slightly
    for text in ax.texts:
        txt = text.get_text()
        if txt in names.values():
            x, y = text.get_position()
            text.set_position((x, y + 0.08))
            text.set_fontsize(15)
            text.set_fontweight("bold")
        else:
            text.set_fontsize(15)
            text.set_fontweight("bold")

    # Create 2x2 legend just below the diagram with minimal spacing
    legend_elements = [
        Patch(facecolor=colorblind_palette[0], label=names["llvmbench"], alpha=0.6),
        Patch(facecolor=colorblind_palette[1], label=names["rtbench"], alpha=0.6),
        Patch(facecolor=colorblind_palette[2], label=names["specbench"], alpha=0.6),
        Patch(facecolor=colorblind_palette[3], label=names["wasmbench"], alpha=0.6),
    ]

    # Position legend closer and tighten figure box
    plt.legend(
        handles=legend_elements,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.02),  # ↓ reduced vertical gap
        ncol=2,
        fontsize=12,
        frameon=False
    )

    # Tighten all paddings and margins
    # plt.subplots_adjust(top=1.0, bottom=0.05, left=0.05, right=0.95)
    # plt.margins(0, 0)
    # ---- Core fix: manually trim ylim (removes top whitespace) ----
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax - (ymax - ymin) * 0.21)  # crop top 25% of whitespace
    ax.set_position([0.05, 0.12, 0.9, 0.8])  # shrink axes to remove outer padding

    plt.savefig("venn4.pdf", dpi=300, bbox_inches="tight", pad_inches=0)
    plt.close()

if __name__ == "__main__":
    main()
