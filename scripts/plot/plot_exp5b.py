#!/usr/bin/env python3
"""
EXP-5b: High-speed ablation (V=70, 100 m/s) — bar chart
Run on server: python3 plot_exp5b.py
Output: ~/H-SA-full-results/exp5b-ablation.png
"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

CSV = '/home/tronghien1011/H-SA-full-results/exp5b-highspeed.csv'
OUT = '/home/tronghien1011/H-SA-full-results/exp5b-ablation.png'

COLS = ['scenario','variant','mobility','maxPaths','numNodes','unk',
        'vMin','vMax','pktInt','simTime','seed',
        'deliveryRatio','avgDelay','throughput','routingOverhead','totalEnergy','extra']

df = pd.read_csv(CSV, header=None, names=COLS, on_bad_lines='skip')
for col in ['deliveryRatio','avgDelay','throughput','routingOverhead','vMax']:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df = df.dropna(subset=['deliveryRatio'])

# Print summary
print("=== Data summary ===")
print(df.groupby(['vMax','variant'])['deliveryRatio'].agg(['mean','std','count']).round(2))

VARIANTS  = ['FULL', 'NOTVI', 'NOSIGMOID', 'SAQMAODV']
LABELS    = ['FULL\n(all components)', 'w/o TVI\n(always EXPLORE)', 'w/o Sigmoid\n(hard threshold)', 'SA-QMAODV\n(no HS mechs)']
COLORS    = ['#2166ac', '#d6604d', '#f4a582', '#888888']
SPEEDS    = [70, 100]
METRICS   = [
    ('deliveryRatio', 'Packet Delivery Ratio (%)', True),
    ('avgDelay',      'Avg End-to-End Delay (ms)', False),
    ('routingOverhead','Routing Overhead (pkts)',   False),
]

fig, axes = plt.subplots(len(METRICS), len(SPEEDS), figsize=(13, 11))
x = np.arange(len(VARIANTS))
W = 0.6

for col_i, V in enumerate(SPEEDS):
    sub = df[df['vMax'] == V]
    for row_i, (metric, ylabel, higher_better) in enumerate(METRICS):
        ax = axes[row_i][col_i]
        means, errs = [], []
        for var in VARIANTS:
            vals = sub[sub['variant'] == var][metric].dropna()
            means.append(vals.mean() if len(vals) > 0 else 0)
            errs.append(vals.std() if len(vals) > 0 else 0)

        bars = ax.bar(x, means, W, yerr=errs, capsize=4,
                      color=COLORS, alpha=0.85, edgecolor='black', linewidth=0.5)

        # Annotate value on bar
        for bar, m in zip(bars, means):
            if m > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(errs)*0.1,
                        f'{m:.1f}', ha='center', va='bottom', fontsize=8, fontweight='bold')

        # Highlight FULL bar
        bars[0].set_edgecolor('#1a3a6b')
        bars[0].set_linewidth(2)

        # Mann-Whitney p-value: FULL vs NOTVI
        full_vals = sub[sub['variant']=='FULL'][metric].dropna()
        notvi_vals = sub[sub['variant']=='NOTVI'][metric].dropna()
        if len(full_vals) > 5 and len(notvi_vals) > 5:
            _, p = stats.mannwhitneyu(full_vals, notvi_vals, alternative='two-sided')
            sig = '***' if p < 0.001 else ('**' if p < 0.01 else ('*' if p < 0.05 else 'ns'))
            # Draw bracket FULL vs NOTVI
            y_top = max(means[0]+errs[0], means[1]+errs[1]) * 1.08
            ax.plot([0, 0, 1, 1], [y_top*0.97, y_top, y_top, y_top*0.97], 'k-', lw=1)
            ax.text(0.5, y_top*1.01, f'p={p:.3f} {sig}', ha='center', va='bottom', fontsize=8, color='red')

        ax.set_xticks(x)
        ax.set_xticklabels(LABELS, fontsize=8)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(f'V = {V} m/s', fontsize=11, fontweight='bold')
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)

# Row labels
for row_i, (metric, ylabel, _) in enumerate(METRICS):
    axes[row_i][0].annotate(ylabel, xy=(0, 0.5), xytext=(-80, 0),
        xycoords='axes fraction', textcoords='offset points',
        ha='right', va='center', fontsize=9, rotation=90)

fig.suptitle('EXP-5b: Ablation Study at High UAV Speeds (N=15, E₀=30 J, 30 seeds)',
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches='tight')
print(f'\nSaved: {OUT}')
print('\nKey finding (FULL vs w/o TVI):')
for V in SPEEDS:
    sub = df[df['vMax']==V]
    f = sub[sub['variant']=='FULL']['deliveryRatio'].mean()
    n = sub[sub['variant']=='NOTVI']['deliveryRatio'].mean()
    print(f'  V={V}: FULL={f:.1f}% vs NOTVI={n:.1f}% (diff={f-n:+.1f}pp)')
