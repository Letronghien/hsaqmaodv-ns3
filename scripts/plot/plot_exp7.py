#!/usr/bin/env python3
"""
EXP-7: Scalability Analysis — Plot metrics vs. number of nodes
Run on server: python3 plot_exp7.py
Output: exp7-scalability.png (4 subplots)
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

CSV = '/home/tronghien1011/H-SA-full-results/exp7-hqa-comparable.csv'
OUT = '/home/tronghien1011/H-SA-full-results/exp7-scalability.png'

COLS = ['scenario','protocol','mobility','maxPaths','numNodes','unk',
        'vMin','vMax','pktInt','simTime','seed',
        'deliveryRatio','avgDelay','throughput','routingOverhead','totalEnergy','extra']

# Load & clean
df = pd.read_csv(CSV, header=None, names=COLS, on_bad_lines='skip')
# Match both EXP7-N (old format) and EXP7_N (new format)
df = df[df['scenario'].str.match(r'EXP7[-_]N', na=False)]

for col in ['numNodes','seed','deliveryRatio','avgDelay','throughput','routingOverhead','totalEnergy']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df = df.dropna(subset=['deliveryRatio','avgDelay','throughput','routingOverhead'])

# Deduplicate: giữ 1 row per (scenario, protocol, seed)
df = df.sort_values('deliveryRatio', ascending=False)
df = df.drop_duplicates(subset=['scenario','protocol','seed'])

# Summary
print("=== Data summary ===")
print(df.groupby(['numNodes','protocol'])['seed'].count().unstack(fill_value=0))
print(f"\nTotal rows: {len(df)}")

PROTOS    = ['AODV','PMAODV','QMAODV','SAQMAODV','HSAQMAODV']
LABELS    = ['AODV','PMAODV','QMAODV','SAQMAODV','H-SAQMAODV']
COLORS    = ['#555555','#2166ac','#4dac26','#d6604d','#b2182b']
MARKERS   = ['o','s','^','D','*']
N_VALS    = sorted(df['numNodes'].unique())

METRICS = [
    ('deliveryRatio',   'Packet Delivery Ratio (%)',   True),
    ('avgDelay',        'Average End-to-End Delay (ms)', False),
    ('throughput',      'Throughput (Mbps)',            True),
    ('routingOverhead', 'Routing Overhead (packets)',   False),
]

fig, axes = plt.subplots(2, 2, figsize=(13, 10))
axes = axes.flatten()

for ax, (metric, ylabel, higher_is_better) in zip(axes, METRICS):
    for proto, label, color, marker in zip(PROTOS, LABELS, COLORS, MARKERS):
        sub = df[df['protocol'] == proto]
        grp = sub.groupby('numNodes')[metric]
        means = grp.mean()
        stds  = grp.std().fillna(0)

        if means.empty:
            continue

        lw = 2.5 if proto == 'HSAQMAODV' else 1.5
        ms = 11  if proto == 'HSAQMAODV' else 7
        zorder = 5 if proto == 'HSAQMAODV' else 2

        ax.errorbar(means.index, means.values, yerr=stds.values,
                    label=label, color=color, marker=marker,
                    linewidth=lw, markersize=ms, capsize=3,
                    zorder=zorder)

    ax.set_xlabel('Number of Nodes (N)', fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_xticks(N_VALS)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(fontsize=9, loc='best')

fig.suptitle('EXP-7: Scalability Analysis (RWP, v=30 m/s, E₀=100 J)',
             fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches='tight')
print(f"\nSaved: {OUT}")
