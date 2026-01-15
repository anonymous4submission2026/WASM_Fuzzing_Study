import pandas as pd
import plotly.graph_objects as go
import numpy as np
import re

# ========= Load Data =========
file_path = "../data/lineage_diagram.tsv"
df = pd.read_csv(file_path, sep="\t")

# Drop rows missing seed_runtime or buggy_runtime
df = df.dropna(subset=["seed_runtime", "buggy_runtime", "mode"])

# ========= Bucket Ages =========
def bucket_age(months):
    bands = {12: "12 months", 24: "24 months", 36: "36 months", 48: "48 months", 72: "72 months"}
    try:
        return bands.get(int(months), None)
    except:
        return None

df["age_band"] = df["avg_seed_age_months"].apply(bucket_age)
df = df.dropna(subset=["age_band"])

# ========= Normalize & Split Runtimes =========
def clean_runtime(raw):
    if pd.isna(raw):
        return []
    parts = str(raw).split("/")
    cleaned = []
    for p in parts:
        p = p.strip()
        p = re.split(r"[ (]", p)[0]
        if p and p not in ["#REF!", "NA", "N/A"]:
            cleaned.append(p)
    return cleaned

# ========= Expand =========
expanded = []
for _, row in df.iterrows():
    seeds = clean_runtime(row["seed_runtime"])
    targets = clean_runtime(row["buggy_runtime"])
    for s in seeds:
        for t in targets:
            expanded.append({
                "seed_runtime": s,
                "age_band": row["age_band"],
                "mode": row["mode"],
                "buggy_runtime": t
            })
df_expanded = pd.DataFrame(expanded)

# ========= Build Layers =========
seed_runtimes = sorted(df_expanded["seed_runtime"].unique())
age_bands = ["12 months", "24 months", "36 months", "48 months", "72 months"]
modes = ["wapplique", "wasmaker", "both_fuzzers", "transplantation"]
target_runtimes = sorted(df_expanded["buggy_runtime"].unique())

nodes_prefixed = (
    [f"seed::{s}" for s in seed_runtimes] +
    [f"age::{a}" for a in age_bands] +
    [f"mode::{m}" for m in modes] +
    [f"target::{t}" for t in target_runtimes]
)
labels = seed_runtimes + age_bands + modes + target_runtimes
node_index = {name: i for i, name in enumerate(nodes_prefixed)}

# ========= Build Links =========
links = {}
link_level = {}

def add_link(src, tgt, stage):
    pair = (node_index[src], node_index[tgt])
    links[pair] = links.get(pair, 0) + 1
    link_level[pair] = stage

for _, row in df_expanded.iterrows():
    add_link(f"seed::{row['seed_runtime']}", f"age::{row['age_band']}", "seed_age")
    add_link(f"age::{row['age_band']}", f"mode::{row['mode']}", "age_mode")
    add_link(f"mode::{row['mode']}", f"target::{row['buggy_runtime']}", "mode_target")

sources = [s for (s, t) in links.keys()]
targets = [t for (s, t) in links.keys()]
values = [v for v in links.values()]

# ========= Node Positions =========
x, y = [], []

def spaced_positions(n):
    return np.linspace(0.1, 0.9, n) if n > 1 else [0.5]

def add_paper_arrow(fig, x0, x1, y, pad=0.04, **arrow_kwargs):
    lay = fig.layout
    plot_w = (lay.width or 1000) - (lay.margin.l or 0) - (lay.margin.r or 0)
    dx_px = ((x1 - pad) - (x0 + pad)) * plot_w
    fig.add_annotation(
        x=(x1 - pad), y=y, xref="paper", yref="paper",     # arrow head just before right text
        ax=-dx_px, ay=0, axref="pixel", ayref="pixel",     # tail just after left text
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=8, arrowcolor="black",
        text="", **arrow_kwargs
    )

# Node positions
for i, n in enumerate(seed_runtimes):
    x.append(0.0)  # far left
    y.append(spaced_positions(len(seed_runtimes))[i])

age_x_map = {
    "12 months": 0.25,
    "24 months": 0.33,
    "36 months": 0.41,
    "48 months": 0.49,
    "72 months": 0.57
}
age_y_map = {
    "12 months": 0.05,
    "24 months": 0.25,
    "36 months": 0.50,
    "48 months": 0.70,
    "72 months": 0.90
}
for i, n in enumerate(age_bands):
    x.append(age_x_map[n])
    y.append(age_y_map[n])

for i, n in enumerate(modes):
    x.append(0.75)  # shifted further right
    y.append(spaced_positions(len(modes))[i])

for i, n in enumerate(target_runtimes):
    x.append(1.0)  # far right
    y.append(spaced_positions(len(target_runtimes))[i])

# ========= Colors =========
palette = ["#4477AA", "#CC6677", "#DDCC77", "#117733", "#88CCEE", "#882255"]
node_colors = []
for i, n in enumerate(seed_runtimes):
    node_colors.append(palette[i % len(palette)])
for _ in age_bands:
    node_colors.append("#BBBBBB")
for _ in modes:
    node_colors.append("#BBBBBB")
for i, n in enumerate(target_runtimes):
    if n in seed_runtimes:
        node_colors.append(palette[seed_runtimes.index(n) % len(palette)])
    else:
        node_colors.append("#999999")

link_colors = []
for (s, t) in links.keys():
    stage = link_level[(s, t)]
    if stage in ["seed_age", "age_mode"]:
        base_color = node_colors[s]
        alpha = 0.6
    else:
        base_color = node_colors[t]
        alpha = 0.4
    if base_color.startswith("#"):
        r = int(base_color[1:3], 16)
        g = int(base_color[3:5], 16)
        b = int(base_color[5:7], 16)
        link_colors.append(f"rgba({r},{g},{b},{alpha})")
    else:
        link_colors.append("rgba(160,160,160,0.4)")

# ========= Build Figure =========
fig = go.Figure(data=[go.Sankey(
    arrangement="fixed",
    node=dict(
        pad=175,
        thickness=20,
        line=dict(color="black", width=5),
        label=labels,
        x=x,
        y=y,
        color=node_colors
    ),
    link=dict(
        source=sources,
        target=targets,
        value=values,
        color=link_colors
    ),
    textfont=dict(size=102, color="black")
)])

fig.update_layout(
    title_text="",
    title_font_size=72,
    font_size=102,
    width=3600,   
    height=900,  
    margin=dict(l=0, r=25, t=50, b=450),
    plot_bgcolor="white",
    annotations=[
        dict(
            text="<b>Seed<br>Runtime</b>",
            x=0.01, y=-0.30, xref="paper", yref="paper",
            showarrow=False, font=dict(size=108, color="black"),
            xanchor="left"
        ),
        dict(
            text="<b>Seed<br>Age</b>",
            x=0.42, y=-0.30, xref="paper", yref="paper",
            showarrow=False, font=dict(size=108, color="black"),
            xanchor="center"
        ),
        dict(
            text="<b>Testing<br>Technique</b>",
            x=0.75, y=-0.30, xref="paper", yref="paper",
            showarrow=False, font=dict(size=108, color="black"),
            xanchor="center"
        ),
        dict(
            text="<b>Buggy<br>Runtime</b>",
            x=1.00, y=-0.30, xref="paper", yref="paper",
            showarrow=False, font=dict(size=108, color="black"),
            xanchor="right"
        )
    ]
)

# Add arrows (same y as labels, trimmed horizontally with pad)
y_labels = -0.18  # in paper coords; adjust and increase bottom margin if clipped
add_paper_arrow(fig, 0.00, 0.34, y=y_labels, pad=0)   # Seed Runtime → Seed Age
add_paper_arrow(fig, 0.35, 0.68, y=y_labels, pad=0)   # Seed Age → Fuzzing/Transplantation
add_paper_arrow(fig, 0.74, 0.90, y=y_labels, pad=0)   # Fuzzing/Transplantation → Buggy Runtime

# ========= Save High-Resolution PDF =========
fig.write_image("testcase_lineage.pdf", format="pdf", width=5600, height=1800, scale=3)  # 300 dpi
