# plot_bugs_cross_runtime_8axes_report_to_reveal_v3.py
import csv
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from dateutil.relativedelta import relativedelta

# ---------- parsing ----------
DATE_FORMATS = [
    "%b-%d-%Y",
    "%B-%d-%Y",
    "%m-%d-%Y",
    "%Y-%m-%d",
    "%b %d %Y",
    "%B %d %Y",
]

RUNTIME_ORDER = ["wamr", "wasmedge", "wasmtime", "wasmer"]
RUNTIME_DISPLAY = {
    "wamr": "WAMR",
    "wasmedge": "WasmEdge",
    "wasmtime": "Wasmtime",
    "wasmer": "Wasmer",
}

# label box colors by runtime (for endpoint tags)
RUNTIME_COLORS = {
    "wamr": "tab:blue",
    "wasmedge": "tab:orange",
    "wasmtime": "tab:purple",
    "wasmer": "tab:cyan",
}

# axis baseline colors
REPORT_AXIS_COLOR = (0.70, 0.83, 1.00, 0.55)  # light blue
REVEAL_AXIS_COLOR = (0.76, 0.93, 0.76, 0.55)  # light green
GRAYED_AXIS_COLOR = (0.85, 0.85, 0.85, 0.65)  # wasmtime-reveal only


def parse_month_anchor(s: str) -> datetime:
    s = (s or "").strip().strip('"').replace("\t", " ")
    if s.endswith(","):
        s = s[:-1].strip()
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(s, fmt)
            return datetime(dt.year, dt.month, 1)  # snap to month
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: {s!r}")


def load_rows_csv(path="bug.csv"):
    """
    CSV (no header), convention:
      reveal_runtime, report_runtime, test_id, report_date, reveal_date
    """
    rows = []
    with open(path, newline="") as f:
        rdr = csv.reader(f)
        for i, row in enumerate(rdr, start=1):
            if not row or all(not c.strip() for c in row):
                continue
            if len(row) < 5:
                raise ValueError(f"Row {i} has fewer than 5 columns: {row}")
            exist_rt = row[0].strip().lower()
            report_rt = row[1].strip().lower()
            test_id = row[2].strip().strip('"')
            t_report = parse_month_anchor(row[3])
            t_exist = parse_month_anchor(row[4])

            if exist_rt not in RUNTIME_ORDER:
                raise ValueError(
                    f"Unknown reveal runtime '{row[0]}' on row {i}. "
                    f"Allowed: {', '.join(RUNTIME_ORDER)}")
            if report_rt not in RUNTIME_ORDER:
                raise ValueError(
                    f"Unknown report runtime '{row[1]}' on row {i}. "
                    f"Allowed: {', '.join(RUNTIME_ORDER)}")
            rows.append({
                "exist_rt": exist_rt,
                "report_rt": report_rt,
                "id": test_id,
                "t_report": t_report,
                "t_exist": t_exist
            })
    if not rows:
        raise ValueError("No data loaded from CSV.")
    return rows


# ---------- axis helpers ----------
def quarter_locator():
    return mdates.MonthLocator(interval=3)  # Q1/Q2/Q3/Q4


def quarter_formatter(x, pos):
    dt = mdates.num2date(x)
    q = (dt.month - 1) // 3 + 1
    return f"Q{q} {dt.year}"


def sym_offset(k: int, step: float) -> float:
    # 1->0, 2->+step, 3->-step, 4->+2*step, 5->-2*step, ...
    if k <= 1:
        return 0.0
    n = k - 1
    mag = (n + 1) // 2
    sign = 1 if n % 2 == 1 else -1
    return sign * mag * step


# ---------- plotting ----------
def plot_bugs_report_to_reveal(
        rows,
        legend_loc=("center left", (1.02, 0.5)),  # outside right
        y_gap=2.0,  # vertical isolation between axes
        y_step=0.88,  # stronger de-overlap for stacked labels
        connect_alpha=0.95,
        save_path="transplantation_timeline.pdf"):
    fig, ax = plt.subplots(figsize=(30, 10))

    # Top 4 = Bug Report timelines; Bottom 4 = Reveal timelines
    total_lines = 8
    base_levels = list(range(total_lines - 1, -1, -1))  # [7..0]
    report_levels = base_levels[:4]  # [7,6,5,4] (TOP)
    exist_levels = base_levels[4:]  # [3,2,1,0] (BOTTOM)

    y_for_report = {
        rt: report_levels[i] * y_gap
        for i, rt in enumerate(RUNTIME_ORDER)
    }
    y_for_exist = {
        rt: exist_levels[i] * y_gap
        for i, rt in enumerate(RUNTIME_ORDER)
    }

    # X range
    xs_all = [r["t_report"] for r in rows] + [r["t_exist"] for r in rows]
    xmin, xmax = min(xs_all), max(xs_all)

    # Snap xmin to January of its year
    xmin = datetime(xmin.year, 1, 1)
    label_offset = relativedelta(months=-5)   # move 5 months further left

    # Baselines + plain captions
    for rt in RUNTIME_ORDER:
        yr = y_for_report[rt]
        ax.hlines(yr, xmin + label_offset, xmax, linewidth=6, color=REPORT_AXIS_COLOR, zorder=0)
        ax.text(xmin + label_offset, yr + 0.65, f"{RUNTIME_DISPLAY[rt]} — Report", ha="left", va="top", fontsize=22, color="black")

        ye = y_for_exist[rt]
        axis_color = GRAYED_AXIS_COLOR if rt == "wasmtime" else REVEAL_AXIS_COLOR
        ax.hlines(ye, xmin + label_offset, xmax, linewidth=6, color=axis_color, zorder=0)
        ax.text(xmin + label_offset, ye + 0.65, f"{RUNTIME_DISPLAY[rt]} — Reveal", ha="left", va="top", fontsize=22, color="black")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(True)
    ax.spines["left"].set_visible(False)

    ax.spines["bottom"].set_position(("outward", 32))

    # Avoid overlap per-axis/per-date
    per_axis_counts = defaultdict(
        int)  # keys: ("report", rt, date) / ("exist", rt, date)

    # Draw arrows and labels
    for r in rows:
        report_rt = r["report_rt"]  # top axis
        exist_rt = r["exist_rt"]  # bottom axis
        x_report = r["t_report"]
        x_exist = r["t_exist"]
        y_report_base = y_for_report[report_rt]
        y_exist_base = y_for_exist[exist_rt]

        # Arrow color: red if existed before report, else green
        arrow_color = "red" if x_exist < x_report else "green"

        # De-overlap offsets
        k_report = ("report", report_rt, x_report)
        per_axis_counts[k_report] += 1
        off_report = sym_offset(per_axis_counts[k_report], y_step)

        k_exist = ("exist", exist_rt, x_exist)
        per_axis_counts[k_exist] += 1
        off_exist = sym_offset(per_axis_counts[k_exist], y_step)

        y1 = y_report_base + off_report  # start at report axis
        y2 = y_exist_base + off_exist  # end at reveal axis

        # ---- ARROW with visible head ----
        # - bigger head via mutation_scale
        # - shrinkB to stop before the target label box
        # - zorder high and clip_off to keep head visible
        ax.annotate(
            "",
            xy=(x_exist, y2),
            xytext=(x_report, y1),
            arrowprops=dict(
                arrowstyle="-|>",  # triangular head
                linestyle="--",
                lw=2.0,
                color=arrow_color,
                alpha=connect_alpha,
                mutation_scale=22,  # head size
                shrinkA=6,  # small gap from start box
                shrinkB=
                18,  # bigger gap near target box (prevents head from being hidden)
            ),
            zorder=3,
            clip_on=False,
        )

        # Endpoint labels (runtime-colored)
        ax.text(x_report,
                y1,
                r["id"],
                ha="center",
                va="center",
                fontsize=17,
                fontweight="bold",
                color="white",
                bbox=dict(boxstyle="round,pad=0.34",
                          facecolor=RUNTIME_COLORS[report_rt],
                          edgecolor="black"),
                zorder=4)
        ax.text(x_exist,
                y2,
                r["id"],
                ha="center",
                va="center",
                fontsize=17,
                fontweight="bold",
                color="white",
                bbox=dict(boxstyle="round,pad=0.34",
                          facecolor=RUNTIME_COLORS[exist_rt],
                          edgecolor="black"),
                zorder=4)

    # Y-axis off
    ax.set_yticks([])

    # Quarterly ticks + note
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.setp(ax.get_xticklabels(), fontsize=22, rotation=30, ha="right")
    # ax.set_xlabel("Timeline", fontsize=17)

    # Hide first two tick labels for visualization purposes
    for lbl in ax.get_xticklabels()[:2]:
        lbl.set_visible(False)

    # Grid
    ax.grid(axis="x", linestyle=":", alpha=0.35, zorder=0)

    # Legend outside right (no overlap)
    arrow_pre, = ax.plot([], [], "--", color="red", label="Existed before report (arrow)")
    arrow_post, = ax.plot([], [], "--", color="green", label="Appeared after report (arrow)")
    # loc, anchor = legend_loc
    ax.legend(
        handles=[arrow_pre, arrow_post],
        loc="lower center",         # bottom inside the axes
        bbox_to_anchor=(0.5, -0.4),  # adjust downward
        ncol=2,                     # horizontal layout
        frameon=False,
        fontsize=28
    )

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    print(f"Saved figure to: {save_path}")


# ---------- main ----------
if __name__ == "__main__":
    data = load_rows_csv("bug.csv")
    plot_bugs_report_to_reveal(data)
