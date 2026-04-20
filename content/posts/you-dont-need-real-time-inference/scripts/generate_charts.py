"""
Generate charts for the Batch Transform blog post.

Charts:
1. Wall-clock time vs instance count, across different inference latencies
2. Cost per job vs instance count, across different inference latencies
3. Monthly cost comparison: Real-Time Endpoint vs Batch Transform (weekly job)
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# --- Constants ---
TOTAL_ITEMS = 100_000
CONCURRENT_PER_INSTANCE = 4          # max_concurrent_transforms
INSTANCE_COST_PER_HOUR = 0.922       # ml.m5.4xlarge us-east-1
COLD_START_MINUTES = 10              # provisioning + model download
RT_INSTANCE_COUNT = 3                # real-time endpoint baseline
HOURS_PER_WEEK = 168

LATENCIES_SEC = [0.01, 0.1, 1, 10, 30]
LATENCY_LABELS = ["10 ms", "100 ms", "1 s", "10 s", "30 s"]
INSTANCE_COUNTS = [1, 2, 4, 8, 16]

COLORS = ["#00b894", "#0984e3", "#6c5ce7", "#e17055", "#d63031"]

import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DIAGRAMS_DIR = os.path.join(SCRIPT_DIR, "..", "diagrams")
os.makedirs(DIAGRAMS_DIR, exist_ok=True)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 12,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
})


def wall_clock_hours(latency_s, instances):
    """Total wall-clock time including cold start."""
    concurrent = instances * CONCURRENT_PER_INSTANCE
    compute_sec = (TOTAL_ITEMS / concurrent) * latency_s
    return (compute_sec / 3600) + (COLD_START_MINUTES / 60)


def job_cost(latency_s, instances):
    """Cost of a single Batch Transform job."""
    hours = wall_clock_hours(latency_s, instances)
    return instances * hours * INSTANCE_COST_PER_HOUR


def rt_monthly_cost():
    """Monthly cost of always-on real-time endpoint."""
    return RT_INSTANCE_COUNT * HOURS_PER_WEEK * 4.33 * INSTANCE_COST_PER_HOUR


# ──────────────────────────────────────────────
# Chart 1: Wall-Clock Time vs Instance Count
# ──────────────────────────────────────────────
fig1, ax1 = plt.subplots(figsize=(10, 6))

for i, (lat, label) in enumerate(zip(LATENCIES_SEC, LATENCY_LABELS)):
    times = [wall_clock_hours(lat, n) for n in INSTANCE_COUNTS]
    ax1.plot(INSTANCE_COUNTS, times, "o-", color=COLORS[i], label=label,
             linewidth=2.5, markersize=8)

ax1.set_xlabel("Instance Count", fontsize=14)
ax1.set_ylabel("Wall-Clock Time (hours)", fontsize=14)
ax1.set_title(
    f"Batch Transform: Wall-Clock Time vs Instance Count\n"
    f"({TOTAL_ITEMS:,} items, {CONCURRENT_PER_INSTANCE} concurrent/instance, "
    f"+{COLD_START_MINUTES} min cold start)",
    fontsize=14, pad=15,
)
ax1.set_yscale("log")
ax1.set_xticks(INSTANCE_COUNTS)
ax1.yaxis.set_major_formatter(ticker.FuncFormatter(
    lambda y, _: f"{y:,.1f}" if y >= 1 else f"{y:,.2f}"
))
ax1.legend(title="Inference Latency", fontsize=11, title_fontsize=12)
ax1.grid(True, alpha=0.3, which="both")


# Add reference line for 1-hour SLA
ax1.axhline(y=1, color="#636e72", linestyle="--", alpha=0.5, linewidth=1)
ax1.text(16.3, 1, "1-hour SLA", fontsize=10, color="#636e72", va="center")

fig1.tight_layout()
fig1.savefig(os.path.join(DIAGRAMS_DIR, "chart-wallclock-time.png"), dpi=150, bbox_inches="tight")
print("✅ Chart 1 saved: chart-wallclock-time.png")


# ──────────────────────────────────────────────
# Chart 2: Cost Per Job vs Instance Count
# ──────────────────────────────────────────────
fig2, ax2 = plt.subplots(figsize=(10, 6))

for i, (lat, label) in enumerate(zip(LATENCIES_SEC, LATENCY_LABELS)):
    costs = [job_cost(lat, n) for n in INSTANCE_COUNTS]
    ax2.plot(INSTANCE_COUNTS, costs, "s-", color=COLORS[i], label=label,
             linewidth=2.5, markersize=8)

ax2.set_xlabel("Instance Count", fontsize=14)
ax2.set_ylabel("Cost Per Job (USD)", fontsize=14)
ax2.set_title(
    f"Batch Transform: Cost Per Job vs Instance Count\n"
    f"({TOTAL_ITEMS:,} items, ml.m5.4xlarge @ ${INSTANCE_COST_PER_HOUR}/hr, us-east-1)",
    fontsize=14, pad=15,
)
ax2.set_yscale("log")
ax2.set_xticks(INSTANCE_COUNTS)
ax2.yaxis.set_major_formatter(ticker.FuncFormatter(
    lambda y, _: f"${y:,.0f}" if y >= 1 else f"${y:,.2f}"
))
ax2.legend(title="Inference Latency", fontsize=11, title_fontsize=12)
ax2.grid(True, alpha=0.3, which="both")

fig2.tight_layout()
fig2.savefig(os.path.join(DIAGRAMS_DIR, "chart-cost-per-job.png"), dpi=150, bbox_inches="tight")
print("✅ Chart 2 saved: chart-cost-per-job.png")


# ──────────────────────────────────────────────
# Chart 3: Monthly Cost — RT Endpoint vs Batch Transform
# ──────────────────────────────────────────────
fig3, ax3 = plt.subplots(figsize=(12, 6))

rt_cost = rt_monthly_cost()
x = np.arange(len(LATENCY_LABELS))
width = 0.13

for j, n_inst in enumerate(INSTANCE_COUNTS):
    bt_costs = [job_cost(lat, n_inst) * 4.33 for lat in LATENCIES_SEC]  # weekly × 4.33
    bars = ax3.bar(x + j * width, bt_costs, width, label=f"BT: {n_inst} inst",
                   color=COLORS[j % len(COLORS)], alpha=0.85, edgecolor="white")

# Real-time endpoint baseline
ax3.axhline(y=rt_cost, color="#d63031", linestyle="--", linewidth=2.5, alpha=0.8)
ax3.text(len(LATENCY_LABELS) - 0.5, rt_cost + 40,
         f"Real-Time Endpoint (3× always-on): ${rt_cost:,.0f}/mo",
         fontsize=11, color="#d63031", ha="right", fontweight="bold")

ax3.set_xlabel("Inference Latency Per Item", fontsize=14)
ax3.set_ylabel("Monthly Cost (USD)", fontsize=14)
ax3.set_title(
    f"Monthly Cost: Real-Time Endpoint vs Batch Transform (weekly job)\n"
    f"({TOTAL_ITEMS:,} items/week, ml.m5.4xlarge, us-east-1)",
    fontsize=14, pad=15,
)
ax3.set_xticks(x + width * 2)
ax3.set_xticklabels(LATENCY_LABELS)
ax3.set_yscale("log")
ax3.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"${y:,.0f}"))
ax3.legend(title="Batch Transform Config", fontsize=10, title_fontsize=11,
           ncol=3, loc="upper left")
ax3.grid(True, alpha=0.3, axis="y", which="both")

fig3.tight_layout()
fig3.savefig(os.path.join(DIAGRAMS_DIR, "chart-monthly-cost-comparison.png"), dpi=150, bbox_inches="tight")
print("✅ Chart 3 saved: chart-monthly-cost-comparison.png")


# ──────────────────────────────────────────────
# Print summary table for reference
# ──────────────────────────────────────────────
print("\n" + "=" * 80)
print(f"{'Latency':<10} {'Instances':<12} {'Wall-Clock (h)':<16} {'Job Cost ($)':<14} {'Monthly ($)':<12} {'vs RT'}")
print("=" * 80)
for lat, label in zip(LATENCIES_SEC, LATENCY_LABELS):
    for n in INSTANCE_COUNTS:
        wc = wall_clock_hours(lat, n)
        jc = job_cost(lat, n)
        mc = jc * 4.33
        savings = (1 - mc / rt_cost) * 100
        print(f"{label:<10} {n:<12} {wc:<16.2f} {jc:<14.2f} {mc:<12.2f} {savings:+.0f}%")
    print("-" * 80)

print(f"\nReal-Time Endpoint monthly cost: ${rt_cost:,.2f}")
print("Done.")
