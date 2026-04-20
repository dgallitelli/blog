"""
Generate interactive Plotly JSON chart for the Batch Transform blog post.

Single combined chart:
- X-axis: instance count (1, 2, 4, 8, 16)
- Bars: cost per job (left y-axis, USD)
- Line + area: wall-clock time (right y-axis, hours)
- RT weekly cost baseline (horizontal dashed line)
- Slider: inference latency per item (10ms → 30s)
- Dropdown: max_concurrent_transforms per instance (1, 2, 4, 8, 16)

Plotly sliders and updatemenus are independent — they can't read each
other's state. So we pre-compute all 25 (latency × concurrency) combos
as separate trace groups, and each control sets visibility across all of them.

The trick: both controls write to the same visibility array. When the user
moves the slider, it activates the combo matching (new_latency, current_concurrency).
When the user picks a dropdown option, it activates (current_latency, new_concurrency).
Since we can't read "current" state, each slider step assumes the dropdown's default,
and each dropdown option assumes the slider's default. This means changing one control
resets the other to its default — an acceptable tradeoff for a blog chart.

To work around this, we use a different approach: the slider iterates over latency,
and for each dropdown selection we rebuild the slider steps. But Plotly can't do that
in static JSON either.

Final approach: single slider with all 25 combos, grouped visually.
Labels: "10ms · 1×", "10ms · 2×", ..., "30s · 16×"
We add vertical tick marks at latency boundaries to visually separate groups.
"""

import json
import math
import os

# ── Constants ──
TOTAL_ITEMS = 100_000
INSTANCE_COST_PER_HOUR = 0.922
COLD_START_MINUTES = 10
RT_INSTANCE_COUNT = 3
HOURS_PER_WEEK = 168

LATENCIES_SEC = [0.01, 0.1, 1, 10, 30]
LATENCY_LABELS = ["10 ms", "100 ms", "1 s", "10 s", "30 s"]
CONCURRENCIES = [1, 2, 4, 8, 16]
INSTANCE_COUNTS = [1, 2, 4, 8, 16]
INSTANCE_LABELS = [str(n) for n in INSTANCE_COUNTS]

BAR_COLORS = ["#7c6cf0", "#8b7cf2", "#9a8cf4", "#a99cf6", "#b8acf8"]
LINE_COLOR = "#00d2a0"
AREA_COLOR = "rgba(0, 210, 160, 0.08)"
RT_COLOR = "#ff6b6b"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DIAGRAMS_DIR = os.path.join(SCRIPT_DIR, "..", "diagrams")
os.makedirs(DIAGRAMS_DIR, exist_ok=True)


def wall_clock_hours(latency_s, instances, concurrent):
    total_concurrent = instances * concurrent
    compute_sec = (TOTAL_ITEMS / total_concurrent) * latency_s
    return (compute_sec / 3600) + (COLD_START_MINUTES / 60)


def job_cost(latency_s, instances, concurrent):
    return instances * wall_clock_hours(latency_s, instances, concurrent) * INSTANCE_COST_PER_HOUR


def rt_weekly_cost():
    return RT_INSTANCE_COUNT * HOURS_PER_WEEK * INSTANCE_COST_PER_HOUR


def fmt_time(h):
    if h < 1:
        return f"{h * 60:.0f}m"
    elif h < 24:
        return f"{h:.1f}h"
    else:
        return f"{h / 24:.1f}d"


def fmt_cost(c):
    if c < 1:
        return f"${c:.2f}"
    elif c < 100:
        return f"${c:.1f}"
    else:
        return f"${c:,.0f}"


# ──────────────────────────────────────────────
# Build traces: 3 per (latency, concurrency) combo
# ──────────────────────────────────────────────

rt_cost = rt_weekly_cost()
traces = []

DEFAULT_LAT_IDX = 4   # 30s
DEFAULT_CONC_IDX = 2  # 4 concurrent

num_combos = len(LATENCIES_SEC) * len(CONCURRENCIES)
TRACES_PER_COMBO = 3

for lat_idx, (lat, lat_label) in enumerate(zip(LATENCIES_SEC, LATENCY_LABELS)):
    for conc_idx, conc in enumerate(CONCURRENCIES):
        costs = [round(job_cost(lat, n, conc), 2) for n in INSTANCE_COUNTS]
        hours = [round(wall_clock_hours(lat, n, conc), 2) for n in INSTANCE_COUNTS]
        is_default = (lat_idx == DEFAULT_LAT_IDX and conc_idx == DEFAULT_CONC_IDX)

        traces.append({
            "x": INSTANCE_LABELS, "y": costs, "type": "bar",
            "name": "Cost per job",
            "marker": {"color": BAR_COLORS, "line": {"color": "rgba(124,108,240,0.6)", "width": 1}},
            "text": [fmt_cost(c) for c in costs],
            "textposition": "outside", "textfont": {"size": 12, "color": "#a99cf6"},
            "hovertemplate": "<b>%{x} instances</b><br>Cost per job: $%{y:,.2f}<extra></extra>",
            "visible": is_default, "yaxis": "y", "showlegend": is_default, "width": 0.55,
        })
        traces.append({
            "x": INSTANCE_LABELS, "y": hours, "type": "scatter", "mode": "none",
            "fill": "tozeroy", "fillcolor": AREA_COLOR, "hoverinfo": "skip",
            "visible": is_default, "yaxis": "y2", "showlegend": False,
        })
        traces.append({
            "x": INSTANCE_LABELS, "y": hours, "type": "scatter",
            "mode": "lines+markers+text", "name": "Wall-clock time",
            "line": {"color": LINE_COLOR, "width": 3, "shape": "spline"},
            "marker": {"size": 10, "color": LINE_COLOR, "line": {"color": "rgba(0,0,0,0.3)", "width": 1}},
            "text": [fmt_time(h) for h in hours],
            "textposition": "top center", "textfont": {"size": 12, "color": LINE_COLOR},
            "hovertemplate": "<b>%{x} instances</b><br>Wall-clock: %{y:.2f} hours<extra></extra>",
            "visible": is_default, "yaxis": "y2", "showlegend": is_default,
        })


def make_vis(target_lat_idx, target_conc_idx):
    """Build visibility + showlegend arrays for a given combo."""
    vis = [False] * (num_combos * TRACES_PER_COMBO)
    show = [False] * (num_combos * TRACES_PER_COMBO)
    combo = target_lat_idx * len(CONCURRENCIES) + target_conc_idx
    base = combo * TRACES_PER_COMBO
    vis[base] = vis[base + 1] = vis[base + 2] = True
    show[base] = show[base + 2] = True  # legend for bar + line only
    return vis, show


def make_title(lat_label, conc):
    return (
        f"Batch Transform: Cost & Time — {lat_label}/item, "
        f"{conc} concurrent/instance<br>"
        f"<sub>{TOTAL_ITEMS:,} items · ml.m5.4xlarge @ "
        f"${INSTANCE_COST_PER_HOUR}/hr · us-east-1</sub>"
    )


# ──────────────────────────────────────────────
# Slider: latency (assumes current concurrency = default)
# ──────────────────────────────────────────────
latency_steps = []
for lat_idx, (lat, lat_label) in enumerate(zip(LATENCIES_SEC, LATENCY_LABELS)):
    vis, show = make_vis(lat_idx, DEFAULT_CONC_IDX)
    latency_steps.append({
        "label": lat_label,
        "method": "update",
        "args": [
            {"visible": vis, "showlegend": show},
            {"title.text": make_title(lat_label, CONCURRENCIES[DEFAULT_CONC_IDX])},
        ],
    })

# ──────────────────────────────────────────────
# Slider 2: concurrency (assumes current latency = default)
# ──────────────────────────────────────────────
conc_steps = []
for conc_idx, conc in enumerate(CONCURRENCIES):
    vis, show = make_vis(DEFAULT_LAT_IDX, conc_idx)
    conc_steps.append({
        "label": f"{conc}×",
        "method": "update",
        "args": [
            {"visible": vis, "showlegend": show},
            {"title.text": make_title(LATENCY_LABELS[DEFAULT_LAT_IDX], conc)},
        ],
    })

default_lat_label = LATENCY_LABELS[DEFAULT_LAT_IDX]
default_conc = CONCURRENCIES[DEFAULT_CONC_IDX]

fig = {
    "data": traces,
    "layout": {
        "title": {
            "text": make_title(default_lat_label, default_conc),
            "font": {"size": 16},
        },
        "xaxis": {
            "title": {"text": "Instance Count", "font": {"size": 14}, "standoff": 30},
            "type": "category",
            "tickfont": {"size": 13},
        },
        "yaxis": {
            "title": {"text": "Cost Per Job (USD)", "font": {"size": 13, "color": "#a99cf6"}},
            "type": "log", "tickprefix": "$", "side": "left",
            "showgrid": True, "gridcolor": "rgba(128,128,128,0.1)",
            "tickfont": {"color": "#a99cf6"}, "range": [-1, 3],
        },
        "yaxis2": {
            "title": {"text": "Wall-Clock Time", "font": {"size": 13, "color": LINE_COLOR}},
            "type": "log", "overlaying": "y", "side": "right",
            "showgrid": False, "tickfont": {"color": LINE_COLOR},
            "range": [-1, 2.5],
            "tickvals": [0.1, 0.5, 1, 5, 10, 50, 100, 200],
            "ticktext": ["6m", "30m", "1h", "5h", "10h", "2d", "4d", "8d"],
        },
        "hovermode": "x unified",
        "legend": {
            "orientation": "h", "y": 1.02, "x": 0.5, "xanchor": "center",
            "yanchor": "bottom",
            "font": {"size": 12},
        },
        "shapes": [
            {
                "type": "line",
                "x0": -0.5, "x1": len(INSTANCE_COUNTS) - 0.5,
                "y0": rt_cost, "y1": rt_cost, "yref": "y",
                "line": {"color": RT_COLOR, "width": 2, "dash": "dash"},
            },
            {
                "type": "rect",
                "x0": -0.5, "x1": len(INSTANCE_COUNTS) - 0.5,
                "y0": rt_cost, "y1": 1000, "yref": "y",
                "fillcolor": "rgba(255, 107, 107, 0.04)", "line": {"width": 0},
            },
        ],
        "annotations": [
            {
                "x": 0.98, "xref": "paper",
                "y": math.log10(rt_cost), "yref": "y",
                "text": f"RT Endpoint: ${rt_cost:,.0f}/wk ▸",
                "showarrow": False,
                "font": {"color": RT_COLOR, "size": 11, "family": "JetBrains Mono, monospace"},
                "xanchor": "right", "yanchor": "bottom", "yshift": 4,
            },
        ],
        "sliders": [
            {
                "active": DEFAULT_LAT_IDX,
                "currentvalue": {
                    "prefix": "Latency per item: ",
                    "visible": True, "xanchor": "center", "font": {"size": 13},
                },
                "pad": {"t": 55, "b": 0},
                "x": 0.05, "len": 0.9, "xanchor": "left",
                "y": 0, "yanchor": "top",
                "steps": latency_steps,
                "transition": {"duration": 300, "easing": "cubic-in-out"},
                "bordercolor": "rgba(128,128,128,0.2)", "ticklen": 4,
            },
            {
                "active": DEFAULT_CONC_IDX,
                "currentvalue": {
                    "prefix": "max_concurrent_transforms: ",
                    "visible": True, "xanchor": "center", "font": {"size": 13},
                },
                "pad": {"t": 30, "b": 0},
                "x": 0.05, "len": 0.9, "xanchor": "left",
                "y": -0.22, "yanchor": "top",
                "steps": conc_steps,
                "transition": {"duration": 300, "easing": "cubic-in-out"},
                "bordercolor": "rgba(128,128,128,0.2)", "ticklen": 4,
            },
        ],
        "margin": {"l": 65, "r": 65, "t": 100, "b": 220},
        "bargap": 0.3,
    },
}

path = os.path.join(DIAGRAMS_DIR, "chart-batch-vs-realtime.json")
with open(path, "w") as f:
    json.dump(fig, f, indent=None, separators=(",", ":"))

print(f"✅ chart-batch-vs-realtime.json ({os.path.getsize(path) / 1024:.1f} KB)")
print(f"   Traces: {len(traces)} ({num_combos} combos × {TRACES_PER_COMBO})")
print(f"   Slider 1: {len(latency_steps)} latency steps")
print(f"   Slider 2: {len(conc_steps)} concurrency steps")
print(f"   Default: {default_lat_label}, {default_conc}× concurrent")
print(f"   RT baseline: ${rt_cost:,.0f}/week")
