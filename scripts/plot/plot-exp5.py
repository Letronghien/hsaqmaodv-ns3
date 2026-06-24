#!/usr/bin/env python3
"""
plot-exp5.py — EXP-5 Ablation Study plotter
Usage: python3 plot-exp5.py ~/H-SA-full-results/exp5-ablation.csv --outdir ~/H-SA-figures
"""
import argparse, os, re
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

VARIANTS = ['FULL', 'noTVI', 'noSigmoid', 'noCongestion', 'noDualQ']
VARIANT_LABELS = {
    'FULL':        'FULL\n(baseline)',
    'noTVI':       'w/o TVI',
    'noSigmoid':   'w/o Sigmoid',
    'noCongestion':'w/o Congestion',
    'noDualQ':     'w/o DualQ',
}
COLORS_V = {20: '#E8722A', 50: '#4878CF'}
METRICS = [
    ('deliveryRatio',   'Delivery Ratio (%)',     '↑ higher = better'),
    ('avgDelayMs',      'Avg Delay (ms)',          '↓ lower = better'),
    ('throughputMbps',  'Throughput (Mbps)',       '↑ higher = better'),
    ('routingOverhead', 'Routing Overhead (pkts)', '↓ lower = better'),
    ('totalEnergyJ',    'Total Energy (J)',        '↓ lower = better'),
]

def parse_scenario(s):
    # EXP5-FULL-V20, EXP5-noTVI-V50, ...
    m = re.match(r'EXP5-([^-]+(?:-[^V][^-]*)*)-V(\d+)', str(s))
    if m:
        return m.group(1), int(m.group(2))
    return None, None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('csvfile')
    parser.add_argument('--outdir', default='./H-SA-figures')
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    df = pd.read_csv(args.csvfile)
    print(f"Loaded: {len(df)} rows | Columns: {df.columns.tolist()}")

    # Parse variant and speed from scenario
    parsed = df['scenario'].apply(parse_scenario)
    df['variant'] = parsed.apply(lambda x: x[0])
    df['speed']   = parsed.apply(lambda x: x[1])
    df = df.dropna(subset=['variant', 'speed'])
    df['speed'] = df['speed'].astype(int)

    print(f"Variants found: {df['variant'].unique().tolist()}")
    print(f"Speeds found:   {df['speed'].unique().tolist()}")
    print(f"Seeds: {df['seed'].nunique()}")

    # Only keep known variants in order
    variants_present = [v for v in VARIANTS if v in df['variant'].unique()]
    speeds = sorted(df['speed'].unique())

    n_metrics = len([m for m in METRICS if m[0] in df.columns])
    ncols = 3
    nrows = (n_metrics + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(16, 5*nrows))
    axes = axes.flatten()

    ax_idx = 0
    bar_width = 0.35
    x = np.arange(len(variants_present))

    for metric, ylabel, note in METRICS:
        if metric not in df.columns:
            continue
        ax = axes[ax_idx]
        df[metric] = pd.to_numeric(df[metric], errors='coerce')

        for si, spd in enumerate(speeds):
            sub = df[df['speed'] == spd]
            means, stds = [], []
            for v in variants_present:
                vals = sub[sub['variant'] == v][metric].dropna()
                means.append(vals.mean())
                stds.append(vals.std() if len(vals) > 1 else 0)

            offset = (si - len(speeds)/2 + 0.5) * bar_width
            bars = ax.bar(x + offset, means, bar_width,
                          label=f'Speed {spd} m/s',
                          color=COLORS_V.get(spd, f'C{si}'),
                          alpha=0.85, yerr=stds, capsize=3,
                          error_kw={'elinewidth':1.2})

            # Annotate FULL value for reference
            if si == 0 and means:
                ax.axhline(means[0], color=COLORS_V.get(spd,'gray'),
                           linestyle=':', linewidth=0.8, alpha=0.5)

        ax.set_xticks(x)
        ax.set_xticklabels([VARIANT_LABELS.get(v, v) for v in variants_present],
                           fontsize=8)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_title(f'{ylabel}\n({note})', fontsize=9, fontweight='bold')
        ax.legend(fontsize=8)
        ax.grid(axis='y', alpha=0.3)

        # Highlight FULL bar with a box
        ax.axvspan(-0.5, 0.5, alpha=0.06, color='green')

        ax_idx += 1

    for i in range(ax_idx, len(axes)):
        axes[i].set_visible(False)

    nseeds = df['seed'].nunique()
    fig.suptitle(f'EXP-5: Ablation Study  (seeds={nseeds}, HSAQMAODV only)',
                 fontsize=13, fontweight='bold')
    plt.tight_layout()

    out = os.path.join(args.outdir, 'exp5-ablation.png')
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\n→ Saved: {out}")

    # Print summary table
    print("\n=== Summary (mean over seeds) ===")
    for spd in speeds:
        print(f"\n--- Speed {spd} m/s ---")
        sub = df[df['speed'] == spd]
        tbl = sub.groupby('variant')[['deliveryRatio','avgDelayMs','throughputMbps']].mean()
        tbl = tbl.reindex([v for v in variants_present if v in tbl.index])
        print(tbl.round(3).to_string())

if __name__ == '__main__':
    main()
