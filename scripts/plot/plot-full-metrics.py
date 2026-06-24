#!/usr/bin/env python3
"""
plot-full-metrics.py
Vẽ đầy đủ 5 metrics x 5 families = 25+ figures
Metrics: PDR, avgDelayMs, routingOverhead, energyConsumedJ, throughputKbps

Usage:
  python3 ~/plot-full-metrics.py ~/results-fullmetrics-*/merged-*.csv --outdir ~/figures-fullmetrics
  python3 ~/plot-full-metrics.py ~/results-fullmetrics-*/merged-N.csv --outdir ~/figures-fullmetrics --family N
"""

import argparse, os, sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ── Protocol styles ───────────────────────────────────────────────────────────
PROTO_STYLES = {
    "AODV":         {"label": "AODV",        "color": "#1f77b4", "marker": "o",  "ls": "-"},
    "PMAODV-3":     {"label": "PMAODV",       "color": "#ff7f0e", "marker": "s",  "ls": "--"},
    "QMAODV-3":     {"label": "QMAODV",       "color": "#2ca02c", "marker": "^",  "ls": "-."},
    "SA-QMAODV-3":  {"label": "SA-QMAODV",    "color": "#9467bd", "marker": "D",  "ls": ":"},
    "H-SAQMAODV-3": {"label": "H-SAQMAODV",   "color": "#d62728", "marker": "*",  "ls": "-",
                     "linewidth": 2.2},
}

# ── Metric configs ────────────────────────────────────────────────────────────
METRICS = {
    "pdr":              {"label": "PDR (%)",                    "scale": 100, "ylim": (0, 110)},
    "avgDelayMs":       {"label": "Avg End-to-End Delay (ms)",  "scale": 1,   "ylim": None},
    "routingOverhead":  {"label": "Routing Overhead (pkts)",    "scale": 1,   "ylim": None},
    "nrl":              {"label": "Normalized Routing Load",    "scale": 1,   "ylim": None},
    "energyConsumedJ":  {"label": "Energy Consumed (J)",        "scale": 1,   "ylim": None},
    "throughputKbps":   {"label": "Throughput (kbps)",          "scale": 1,   "ylim": None},
}

# Alias mapping: handle different column names
COL_ALIASES = {
    "pdr":             ["pdr", "PDR", "pkt_delivery_ratio", "deliveryRatio"],
    "avgDelayMs":      ["avgDelayMs", "avgDelay", "avg_delay", "delay", "e2eDelay", "endToEndDelay"],
    "routingOverhead": ["routingOverhead", "ctrlPktCount", "ctrlPackets", "overhead"],
    "nrl":             ["nrl", "NRL", "normalizedRoutingLoad"],
    "energyConsumedJ": ["energyConsumedJ", "energyConsumed", "energyTotal", "totalEnergy"],
    "throughputKbps":  ["throughputKbps", "throughput", "avgThroughput"],
}

def resolve_col(df, metric):
    for alias in COL_ALIASES.get(metric, [metric]):
        if alias in df.columns:
            return alias
    return None

# ── Family definitions ────────────────────────────────────────────────────────
FAMILY_CONFIGS = {
    "N": {
        "x_extract": lambda row: float(re.search(r'N-N(\d+)', row).group(1)) if re.search(r'N-N(\d+)', row) else None,
        "x_label": "Number of Nodes",
        "prefix": "N-",
    },
    "S": {
        "x_extract": lambda row: float(re.search(r'S-.*V(\d+)', row).group(1)) if re.search(r'S-.*V(\d+)', row) else None,
        "x_label": "Mean Speed (m/s)",
        "prefix": "S-",
    },
    "E": {
        "x_extract": lambda row: float(re.search(r'E-.*E(\d+)', row).group(1)) if re.search(r'E-.*E(\d+)', row) else None,
        "x_label": "Initial Battery (J)",
        "prefix": "E-",
    },
    "L": {
        "x_extract": lambda row: float(re.search(r'L-.*I([0-9.]+)', row).group(1)) if re.search(r'L-.*I([0-9.]+)', row) else None,
        "x_label": "Packet Interval (s)",
        "prefix": "L-",
    },
    "HQA": {
        "x_extract": lambda row: float(re.search(r'HQA-N(\d+)', row).group(1)) if re.search(r'HQA-N(\d+)', row) else None,
        "x_label": "Number of Nodes",
        "prefix": "HQA-",
    },
}

import re

def detect_family(df):
    """Detect family from 'scenario' column prefix."""
    if "scenario" not in df.columns:
        return None
    sample = df["scenario"].dropna().iloc[0] if len(df) > 0 else ""
    for fam, cfg in FAMILY_CONFIGS.items():
        if sample.startswith(cfg["prefix"]) or f"-{fam}-" in sample or f"_{fam}_" in sample:
            return fam
    # fallback: try column name patterns
    for fam in ["N", "S", "E", "L", "HQA"]:
        if df["scenario"].str.contains(f"^{fam}-", regex=True).any():
            return fam
    return None

def extract_x(df, family):
    cfg = FAMILY_CONFIGS.get(family)
    if cfg is None:
        return None
    try:
        df = df.copy()
        df["_x"] = df["scenario"].apply(cfg["x_extract"])
        return df
    except Exception:
        return None

def plot_metric_family(df, family, metric, outdir, metric_cfg):
    col = resolve_col(df, metric)
    if col is None:
        print(f"  [SKIP] {metric} not found in columns: {list(df.columns)}")
        return

    df2 = extract_x(df, family)
    if df2 is None or "_x" not in df2.columns:
        print(f"  [SKIP] Cannot extract x-axis for family {family}")
        return

    df2 = df2.dropna(subset=["_x", col])
    df2[col] = pd.to_numeric(df2[col], errors="coerce")
    df2 = df2.dropna(subset=[col])

    scale = metric_cfg.get("scale", 1)
    df2[col] = df2[col] * scale

    # Detect protocol column
    proto_col = next((c for c in ["protocol", "Protocol", "proto"] if c in df2.columns), None)
    if proto_col is None:
        print(f"  [SKIP] No protocol column")
        return

    agg = df2.groupby([proto_col, "_x"])[col].agg(["mean", "std"]).reset_index()

    fig, ax = plt.subplots(figsize=(7, 4.5))
    plotted = 0
    for proto, style in PROTO_STYLES.items():
        d = agg[agg[proto_col] == proto].sort_values("_x")
        if d.empty:
            continue
        lw = style.get("linewidth", 1.8)
        ax.errorbar(d["_x"], d["mean"], yerr=d["std"].fillna(0),
                    label=style["label"], color=style["color"],
                    marker=style["marker"], linestyle=style["ls"],
                    capsize=4, linewidth=lw)
        plotted += 1

    if plotted == 0:
        plt.close(fig)
        return

    cfg = FAMILY_CONFIGS[family]
    ax.set_xlabel(cfg["x_label"], fontsize=12)
    ax.set_ylabel(metric_cfg["label"], fontsize=12)
    ax.set_title(f"{metric_cfg['label']} vs {cfg['x_label']}", fontsize=13)
    if metric_cfg.get("ylim"):
        ax.set_ylim(*metric_cfg["ylim"])
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.4)
    fig.tight_layout()

    fname = f"fig_{family.lower()}_{metric}.pdf"
    fpath = os.path.join(outdir, fname)
    fig.savefig(fpath, dpi=150)
    plt.close(fig)
    print(f"  [OK] {fpath}")

# ── TVI heatmap ───────────────────────────────────────────────────────────────
def plot_tvi_heatmap(df, outdir):
    pdr_col = resolve_col(df, "pdr")
    if pdr_col is None:
        return
    # Extract tviHigh, tviLow from scenario
    def get_tvi(s):
        m1 = re.search(r'h(\d+)', s)
        m2 = re.search(r'l(\d+)', s)
        if m1 and m2:
            return int(m1.group(1)), int(m2.group(1))
        return None, None

    df2 = df.copy()
    df2[pdr_col] = pd.to_numeric(df2[pdr_col], errors="coerce") * 100
    df2[["tviHigh", "tviLow"]] = df2["scenario"].apply(
        lambda s: pd.Series(get_tvi(s)))
    df2 = df2.dropna(subset=["tviHigh", "tviLow", pdr_col])
    if df2.empty:
        return

    pivot = df2.groupby(["tviHigh", "tviLow"])[pdr_col].mean().unstack()

    fig, ax = plt.subplots(figsize=(7, 5))
    im = ax.imshow(pivot.values, cmap="Blues", aspect="auto", vmin=25, vmax=40)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([f"tviLow={v}" for v in pivot.columns])
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([f"tviHigh={v}" for v in pivot.index])
    plt.colorbar(im, ax=ax, label="PDR (%)")

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.iloc[i, j]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.1f}", ha="center", va="center", fontsize=9,
                        color="white" if val > 33 else "black")

    ax.set_title("PDR (%) vs TVI Thresholds — H-SAQMAODV", fontsize=13)
    fig.tight_layout()
    fpath = os.path.join(outdir, "fig_TVI_heatmap_pdr.pdf")
    fig.savefig(fpath, dpi=150)
    plt.close(fig)
    print(f"  [OK] {fpath}")

# ── Summary subplot: 1 family, all metrics ────────────────────────────────────
def plot_summary_panel(df, family, outdir):
    """6-panel figure: PDR + Delay + Overhead + NRL + Energy + Throughput"""
    metric_list = ["pdr", "avgDelayMs", "nrl", "energyConsumedJ", "throughputKbps", "routingOverhead"]
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    axes = axes.flatten()

    proto_col = next((c for c in ["protocol", "Protocol"] if c in df.columns), None)
    if proto_col is None:
        return

    df2 = extract_x(df, family)
    if df2 is None:
        return
    df2 = df2.dropna(subset=["_x"])

    plotted_panel = False
    for idx, metric in enumerate(metric_list):
        ax = axes[idx]
        col = resolve_col(df2, metric)
        m_cfg = METRICS.get(metric, {"label": metric, "scale": 1, "ylim": None})

        if col is None:
            ax.text(0.5, 0.5, f"{metric}\nnot available", ha="center", va="center",
                    transform=ax.transAxes, fontsize=10, color="gray")
            ax.set_title(m_cfg["label"])
            continue

        df3 = df2.dropna(subset=[col]).copy()
        df3[col] = pd.to_numeric(df3[col], errors="coerce") * m_cfg["scale"]
        df3 = df3.dropna(subset=[col])
        agg = df3.groupby([proto_col, "_x"])[col].agg(["mean", "std"]).reset_index()

        for proto, style in PROTO_STYLES.items():
            d = agg[agg[proto_col] == proto].sort_values("_x")
            if d.empty:
                continue
            ax.errorbar(d["_x"], d["mean"], yerr=d["std"].fillna(0),
                        label=style["label"], color=style["color"],
                        marker=style["marker"], linestyle=style["ls"],
                        capsize=3, linewidth=1.6)
            plotted_panel = True

        ax.set_ylabel(m_cfg["label"], fontsize=10)
        ax.set_xlabel(FAMILY_CONFIGS[family]["x_label"], fontsize=10)
        ax.set_title(m_cfg["label"], fontsize=11)
        if m_cfg.get("ylim"):
            ax.set_ylim(*m_cfg["ylim"])
        ax.grid(True, alpha=0.3)

    if plotted_panel:
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=5, fontsize=9,
                   bbox_to_anchor=(0.5, -0.02))
        fig.suptitle(f"Family {family} — Full Metrics", fontsize=14, fontweight="bold")
        fig.tight_layout(rect=[0, 0.05, 1, 1])
        fpath = os.path.join(outdir, f"fig_{family.lower()}_summary.pdf")
        fig.savefig(fpath, dpi=150, bbox_inches="tight")
        print(f"  [OK] {fpath}")
    plt.close(fig)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csvfiles", nargs="+")
    parser.add_argument("--outdir", default="./figures-fullmetrics")
    parser.add_argument("--family", default=None, help="Force family: N/S/E/L/HQA/TVI")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # Load all CSVs
    dfs = []
    for f in args.csvfiles:
        try:
            df = pd.read_csv(f)
            dfs.append(df)
        except Exception as e:
            print(f"[WARN] Cannot read {f}: {e}")

    if not dfs:
        print("[ERROR] No valid CSV files loaded.")
        sys.exit(1)

    all_df = pd.concat(dfs, ignore_index=True)
    print(f"[INFO] Loaded {len(all_df)} rows, columns: {list(all_df.columns)}")

    # Group by family
    if args.family:
        families_to_plot = [args.family]
        family_dfs = {args.family: all_df}
    else:
        # Split by family using 'scenario' prefix
        family_dfs = {}
        if "scenario" in all_df.columns:
            for fam in ["TVI", "N", "S", "E", "L", "HQA"]:
                mask = all_df["scenario"].str.startswith(fam + "-", na=False)
                if mask.any():
                    family_dfs[fam] = all_df[mask].copy()
        if not family_dfs:
            family_dfs = {"ALL": all_df}
        families_to_plot = list(family_dfs.keys())

    print(f"[INFO] Families: {families_to_plot}")

    for fam in families_to_plot:
        df = family_dfs[fam]
        print(f"\n[FAMILY {fam}] rows={len(df)}")

        if fam == "TVI":
            plot_tvi_heatmap(df, args.outdir)
            continue

        # Individual metric figures
        for metric, m_cfg in METRICS.items():
            plot_metric_family(df, fam, metric, args.outdir, m_cfg)

        # Summary panel
        plot_summary_panel(df, fam, args.outdir)

    print(f"\n[DONE] Figures saved to: {args.outdir}")

if __name__ == "__main__":
    main()
