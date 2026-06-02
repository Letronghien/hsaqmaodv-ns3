#!/usr/bin/env python3
"""
plot-paper1.py — Generate all figures for H-SAQMAODV Paper 1.

Usage:
    python3 plot-paper1.py <merged.csv> [--outdir ./figures]

Produces:
    fig2_tvi_heatmap.pdf     — TVI threshold sensitivity heatmap
    fig3_pdr_vs_n.pdf        — PDR vs node density
    fig4_pdr_vs_speed.pdf    — PDR vs mobility speed
    fig5_pdr_vs_energy.pdf   — PDR vs initial energy (hetero-battery)
    fig6_mode_distribution.pdf — Mode distribution (if mode data available)
    fig_pdr_vs_load.pdf      — PDR vs traffic load (supplementary)
"""

import sys
import os
import csv
import argparse
import warnings
from collections import defaultdict
from itertools import product

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
warnings.filterwarnings('ignore')

# ─── Style ──────────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 11,
    'axes.titlesize': 12,
    'axes.labelsize': 11,
    'legend.fontsize': 9,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.dpi': 150,
    'savefig.bbox': 'tight',
    'savefig.dpi': 300,
})

# Protocol display config
PROTO_STYLE = {
    'AODV':         {'color': '#555555', 'marker': 's', 'ls': '-',  'lw': 1.5, 'label': 'AODV'},
    'AOMDV-3':      {'color': '#E67E22', 'marker': '^', 'ls': '--', 'lw': 1.5, 'label': 'AOMDV-3'},
    'QMAODV-3':     {'color': '#2980B9', 'marker': 'o', 'ls': '--', 'lw': 1.5, 'label': 'QMAODV-3'},
    'SAQMAODV-3':   {'color': '#27AE60', 'marker': 'D', 'ls': '-.',  'lw': 1.5, 'label': 'SA-QMAODV-3'},
    'HSAQMAODV-3':  {'color': '#C0392B', 'marker': '*', 'ls': '-',  'lw': 2.0, 'label': 'H-SAQMAODV-3 (Proposed)'},
}
PROTO_ORDER = list(PROTO_STYLE.keys())


# ─── Data Loading ───────────────────────────────────────────────────────────
def load_csv(path):
    rows = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def label_of(proto, mp):
    if proto == 'AODV':
        return 'AODV'
    return f"{proto}-{mp}"


def parse_scenario(scenario):
    """Parse 'FAM-N15-V20-T200-E0' → dict"""
    parts = scenario.split('-')
    d = {'family': parts[0]}
    for p in parts[1:]:
        for prefix, key in [('N','numNodes'), ('V','speed'), ('T','simTime'), ('E','energy')]:
            if p.startswith(prefix):
                try:
                    d[key] = float(p[len(prefix):])
                except ValueError:
                    pass
    return d


def aggregate(rows, key_fn, val='deliveryRatio'):
    """Group rows by key_fn(row) → mean, std, n"""
    groups = defaultdict(list)
    for r in rows:
        try:
            v = float(r[val])
        except (KeyError, ValueError):
            continue
        k = key_fn(r)
        if k is not None:
            groups[k].append(v)
    result = {}
    for k, vs in groups.items():
        result[k] = (np.mean(vs), np.std(vs), len(vs))
    return result


def filter_family(rows, family):
    out = []
    for r in rows:
        sc = r.get('scenario', '')
        if sc.startswith(family + '-') or sc.startswith(family.upper() + '-'):
            out.append(r)
    return out


# ─── Fig 2: TVI Heatmap ─────────────────────────────────────────────────────
def plot_tvi_heatmap(rows, outdir):
    tvi_rows = filter_family(rows, 'TVI')
    if not tvi_rows:
        print("  [skip] No TVI family data found")
        return

    # Group: (tviHigh, tviLow) → mean PDR for HSAQMAODV
    groups = defaultdict(list)
    for r in tvi_rows:
        if label_of(r.get('protocol',''), r.get('maxPaths','1')) != 'HSAQMAODV-3':
            continue
        try:
            tvh = float(r.get('tviHigh', r.get('hsTviHigh', 0)))
            tvl = float(r.get('tviLow',  r.get('hsTviLow',  0)))
            pdr = float(r['deliveryRatio'])
        except (KeyError, ValueError):
            continue
        groups[(tvh, tvl)].append(pdr)

    if not groups:
        print("  [skip] TVI data present but no HSAQMAODV rows with tviHigh/tviLow columns")
        return

    tvh_vals = sorted({k[0] for k in groups})
    tvl_vals = sorted({k[1] for k in groups})
    matrix = np.full((len(tvl_vals), len(tvh_vals)), np.nan)
    for i, tvl in enumerate(tvl_vals):
        for j, tvh in enumerate(tvh_vals):
            vs = groups.get((tvh, tvl), [])
            if vs:
                matrix[i, j] = np.mean(vs)

    fig, ax = plt.subplots(figsize=(6, 4))
    im = ax.imshow(matrix * 100, aspect='auto', cmap='RdYlGn',
                   vmin=np.nanmin(matrix)*100-2, vmax=np.nanmax(matrix)*100+2)
    ax.set_xticks(range(len(tvh_vals)))
    ax.set_xticklabels([int(v) for v in tvh_vals])
    ax.set_yticks(range(len(tvl_vals)))
    ax.set_yticklabels([int(v) for v in tvl_vals])
    ax.set_xlabel('TVI$_{high}$ threshold')
    ax.set_ylabel('TVI$_{low}$ threshold')
    ax.set_title('Fig 2: PDR (%) vs TVI Thresholds — H-SAQMAODV')
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label('PDR (%)')
    # Annotate cells
    for i in range(len(tvl_vals)):
        for j in range(len(tvh_vals)):
            v = matrix[i, j]
            if not np.isnan(v):
                ax.text(j, i, f'{v*100:.1f}', ha='center', va='center',
                        fontsize=8, color='black')

    # Mark best
    best_idx = np.unravel_index(np.nanargmax(matrix), matrix.shape)
    ax.add_patch(plt.Rectangle((best_idx[1]-0.5, best_idx[0]-0.5), 1, 1,
                                fill=False, edgecolor='blue', lw=2))
    plt.tight_layout()
    path = os.path.join(outdir, 'fig2_tvi_heatmap.pdf')
    plt.savefig(path)
    plt.close()
    print(f"  Saved: {path}")


# ─── Generic Line Plot ───────────────────────────────────────────────────────
def plot_line(agg_data, x_vals, x_label, title, figname, outdir, x_log=False):
    """
    agg_data: dict (proto_label, x_val) → (mean, std, n)
    """
    fig, ax = plt.subplots(figsize=(6, 4))

    for proto in PROTO_ORDER:
        style = PROTO_STYLE.get(proto, {})
        ys, errs, xs = [], [], []
        for x in x_vals:
            key = (proto, x)
            if key in agg_data:
                mean, std, _ = agg_data[key]
                xs.append(x)
                ys.append(mean * 100)
                errs.append(std * 100)
        if not xs:
            continue
        ax.errorbar(xs, ys, yerr=errs,
                    color=style.get('color','black'),
                    marker=style.get('marker','o'),
                    linestyle=style.get('ls','-'),
                    linewidth=style.get('lw',1.5),
                    markersize=6,
                    capsize=3,
                    label=style.get('label', proto))

    ax.set_xlabel(x_label)
    ax.set_ylabel('PDR (%)')
    ax.set_title(title)
    if x_log:
        ax.set_xscale('log')
    ax.legend(loc='best', framealpha=0.8)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 105)

    plt.tight_layout()
    path = os.path.join(outdir, figname)
    plt.savefig(path)
    plt.close()
    print(f"  Saved: {path}")


# ─── Fig 3: PDR vs N ────────────────────────────────────────────────────────
def plot_pdr_vs_n(rows, outdir):
    family_rows = filter_family(rows, 'N')
    if not family_rows:
        print("  [skip] No N family data")
        return

    N_VALS = [5, 8, 10, 15, 20, 25, 30]

    def key_fn(r):
        sc = parse_scenario(r.get('scenario',''))
        n = sc.get('numNodes')
        if n is None:
            return None
        return (label_of(r['protocol'], r['maxPaths']), n)

    agg = aggregate(family_rows, key_fn)
    plot_line(agg, N_VALS, 'Number of Nodes', 'Fig 3: PDR vs Node Density', 'fig3_pdr_vs_n.pdf', outdir)


# ─── Fig 4: PDR vs Speed ────────────────────────────────────────────────────
def plot_pdr_vs_speed(rows, outdir):
    family_rows = filter_family(rows, 'S')
    if not family_rows:
        print("  [skip] No S family data")
        return

    S_VALS = [5, 10, 15, 20, 25, 30, 50]

    def key_fn(r):
        sc = parse_scenario(r.get('scenario',''))
        v = sc.get('speed')
        if v is None:
            return None
        return (label_of(r['protocol'], r['maxPaths']), v)

    agg = aggregate(family_rows, key_fn)
    plot_line(agg, S_VALS, 'Mean Speed (m/s)', 'Fig 4: PDR vs Mobility Speed', 'fig4_pdr_vs_speed.pdf', outdir)


# ─── Fig 5: PDR vs Energy ───────────────────────────────────────────────────
def plot_pdr_vs_energy(rows, outdir):
    family_rows = filter_family(rows, 'E')
    if not family_rows:
        print("  [skip] No E family data")
        return

    E_VALS = [10, 20, 30, 50]

    def key_fn(r):
        sc = parse_scenario(r.get('scenario',''))
        e = sc.get('energy')
        if e is None:
            return None
        return (label_of(r['protocol'], r['maxPaths']), e)

    agg = aggregate(family_rows, key_fn)
    plot_line(agg, E_VALS, 'Initial Energy (J)', 'Fig 5: PDR vs Battery Capacity', 'fig5_pdr_vs_energy.pdf', outdir)


# ─── Fig: PDR vs Load ───────────────────────────────────────────────────────
def plot_pdr_vs_load(rows, outdir):
    family_rows = filter_family(rows, 'L')
    if not family_rows:
        print("  [skip] No L family data")
        return

    # pktInterval stored in scenario or CSV column
    L_VALS = [0.05, 0.1, 0.25, 0.5, 1.0]

    def key_fn(r):
        sc = parse_scenario(r.get('scenario',''))
        # try getting from pktInterval column
        try:
            pkt = float(r.get('pktInterval', sc.get('pktInterval', 0)))
        except ValueError:
            return None
        return (label_of(r['protocol'], r['maxPaths']), pkt)

    agg = aggregate(family_rows, key_fn)
    plot_line(agg, sorted(L_VALS), 'Packet Interval (s)', 'PDR vs Traffic Load', 'fig_pdr_vs_load.pdf', outdir, x_log=True)


# ─── Fig 6: Mode Distribution Bar ───────────────────────────────────────────
def plot_mode_distribution(rows, outdir):
    """
    Requires CSV columns: modeBypass, modeGreedy, modeExplore (counts).
    These are output by the HSAQMAODV simulation when --csvModeStats=1.
    """
    cols = {'modeBypass', 'modeGreedy', 'modeExplore'}
    hsrows = [r for r in rows
              if r.get('protocol','') == 'HSAQMAODV' and cols.issubset(r.keys())]
    if not hsrows:
        print("  [skip] No mode distribution data (need modeBypass/modeGreedy/modeExplore columns)")
        return

    # Group by scenario family
    fam_totals = defaultdict(lambda: [0.0, 0.0, 0.0])
    fam_count = defaultdict(int)
    for r in hsrows:
        fam = r.get('scenario','?').split('-')[0]
        try:
            b = float(r['modeBypass'])
            g = float(r['modeGreedy'])
            e = float(r['modeExplore'])
        except ValueError:
            continue
        total = b + g + e
        if total == 0:
            continue
        fam_totals[fam][0] += b / total
        fam_totals[fam][1] += g / total
        fam_totals[fam][2] += e / total
        fam_count[fam] += 1

    if not fam_totals:
        print("  [skip] Mode data found but no valid rows")
        return

    fams = sorted(fam_totals.keys())
    bypass_f  = [fam_totals[f][0] / fam_count[f] for f in fams]
    greedy_f  = [fam_totals[f][1] / fam_count[f] for f in fams]
    explore_f = [fam_totals[f][2] / fam_count[f] for f in fams]

    x = np.arange(len(fams))
    fig, ax = plt.subplots(figsize=(6, 4))
    width = 0.6
    ax.bar(x, [v*100 for v in bypass_f],  width, label='MODE_BYPASS',  color='#E74C3C')
    ax.bar(x, [v*100 for v in greedy_f],  width, bottom=[v*100 for v in bypass_f],
           label='MODE_GREEDY',  color='#2ECC71')
    ax.bar(x, [v*100 for v in explore_f], width,
           bottom=[(b+g)*100 for b,g in zip(bypass_f, greedy_f)],
           label='MODE_EXPLORE', color='#3498DB')
    ax.set_xticks(x)
    ax.set_xticklabels(fams)
    ax.set_ylabel('Mode Usage (%)')
    ax.set_title('Fig 6: Mode Distribution — H-SAQMAODV')
    ax.legend()
    ax.set_ylim(0, 105)
    plt.tight_layout()
    path = os.path.join(outdir, 'fig6_mode_distribution.pdf')
    plt.savefig(path)
    plt.close()
    print(f"  Saved: {path}")


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='Plot H-SAQMAODV Paper 1 figures')
    parser.add_argument('csv', help='Path to merged.csv from run-paper1-experiments.sh')
    parser.add_argument('--outdir', default='./figures', help='Output directory for figures')
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    print(f"Loading: {args.csv}")
    rows = load_csv(args.csv)
    print(f"  Rows loaded: {len(rows)}")

    # Normalize protocol labels
    for r in rows:
        r['_label'] = label_of(r.get('protocol',''), r.get('maxPaths','1'))

    print(f"\nGenerating figures → {args.outdir}/")
    plot_tvi_heatmap(rows, args.outdir)
    plot_pdr_vs_n(rows, args.outdir)
    plot_pdr_vs_speed(rows, args.outdir)
    plot_pdr_vs_energy(rows, args.outdir)
    plot_pdr_vs_load(rows, args.outdir)
    plot_mode_distribution(rows, args.outdir)
    print("\nDone.")


if __name__ == '__main__':
    main()
