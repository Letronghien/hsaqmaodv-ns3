#!/usr/bin/env python3
"""
plot-results.py — H-SAQMAODV experiment result plotter
Usage: python3 plot-results.py <csv_files...> --outdir <dir>
"""
import argparse, sys, os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PROTO_ORDER  = ['AODV','PMAODV','QMAODV','SAQMAODV','HSAQMAODV']
PROTO_LABELS = {
    'AODV':'AODV', 'PMAODV':'P-MAODV', 'QMAODV':'Q-MAODV',
    'SAQMAODV':'SA-QMAODV', 'HSAQMAODV':'H-SAQMAODV',
}
COLORS   = ['#4878CF','#6ACC65','#D65F5F','#B47CC7','#E8722A']
MARKERS  = ['o','s','^','D','*']
LINES    = ['-','--','-.',':', '-']

METRICS = [
    ('deliveryRatio',  'Delivery Ratio (%)',    None),   # already in %
    ('avgDelayMs',     'Avg Delay (ms)',         None),
    ('throughputMbps', 'Throughput (Mbps)',      None),
    ('routingOverhead','Routing Overhead (pkts)',None),
    ('totalEnergyJ',   'Total Energy (J)',       None),
]

EXP_CFG = {
    'EXP1': dict(col='numNodes',    xlabel='Number of Nodes',   title='EXP-1: Node Density Sweep'),
    'EXP2': dict(col='meanVelMin',  xlabel='Speed (m/s)',        title='EXP-2: Speed Sweep'),
    'EXP3': dict(col='pktInterval', xlabel='Pkt Interval (s)',   title='EXP-3: Traffic Load'),
    'EXP4': dict(col='scenario',    xlabel='Energy config',      title='EXP-4: Battery Capacity'),
    'EXP6': dict(col='scenario',    xlabel='TVI (High,Low)',     title='EXP-6: TVI Sensitivity'),
    'EXP7': dict(col='numNodes',    xlabel='Number of Nodes',    title='EXP-7: HQA-Comparable'),
    'EXP8': dict(col='scenario',    xlabel='Energy config',      title='EXP-8: Energy HQA'),
}


def plot_exp(df_in, key, cfg, outdir, nseeds):
    xcol = cfg['col']
    # fallback: use scenario as x if column missing
    if xcol not in df_in.columns:
        xcol = 'scenario'

    protos = [p for p in PROTO_ORDER if p in df_in['protocol'].unique()]
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    axes = axes.flatten()

    for ax_idx, (metric, ylabel, _) in enumerate(METRICS):
        ax = axes[ax_idx]
        if metric not in df_in.columns:
            ax.set_visible(False)
            continue

        for pi, proto in enumerate(protos):
            sub = df_in[df_in['protocol'] == proto].copy()
            # Force numeric — critical fix
            sub[metric] = pd.to_numeric(sub[metric], errors='coerce')
            grp = sub.groupby(xcol)[metric]
            mean_vals = grp.mean()
            std_vals  = grp.std().fillna(0)

            xv = mean_vals.index.tolist()
            yv = mean_vals.values.copy()
            ye = std_vals.values.copy()

            ax.errorbar(xv, yv, yerr=ye,
                        label=PROTO_LABELS.get(proto, proto),
                        color=COLORS[pi % 5],
                        marker=MARKERS[pi % 5],
                        linestyle=LINES[pi % 5],
                        linewidth=1.8, markersize=7, capsize=4)

        ax.set_xlabel(cfg['xlabel'], fontsize=9)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_title(ylabel, fontsize=9, fontweight='bold')
        ax.legend(fontsize=7)
        ax.grid(alpha=0.3)

    for i in range(len(METRICS), len(axes)):
        axes[i].set_visible(False)

    fig.suptitle(f"{cfg['title']}  (seeds={nseeds})", fontsize=12, fontweight='bold')
    plt.tight_layout()
    out = os.path.join(outdir, f"{key.lower()}.png")
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  → {out}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('csvfiles', nargs='+')
    parser.add_argument('--outdir', default='./H-SA-figures')
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    dfs = []
    for f in args.csvfiles:
        try:
            tmp = pd.read_csv(f)
            print(f"Loaded: {os.path.basename(f)}  ({len(tmp)} rows)")
            dfs.append(tmp)
        except Exception as e:
            print(f"WARN: {f}: {e}")

    if not dfs:
        print("No valid CSVs"); sys.exit(1)

    df = pd.concat(dfs, ignore_index=True)
    nseeds = df['seed'].nunique() if 'seed' in df.columns else '?'
    print(f"\nTotal: {len(df)} rows | Seeds: {nseeds} | Protocols: {df['protocol'].unique().tolist()}\n")

    def get_exp(s):
        for k in EXP_CFG:
            if str(s).startswith(k):
                return k
        return None

    df['_exp'] = df['scenario'].apply(get_exp)

    for key, cfg in EXP_CFG.items():
        sub = df[df['_exp'] == key]
        if sub.empty:
            print(f"  {key}: no data, skip")
            continue
        print(f"Plotting {key} ({len(sub)} rows)...")
        plot_exp(sub, key, cfg, args.outdir, nseeds)

    print(f"\nDone → {args.outdir}")


if __name__ == '__main__':
    main()
