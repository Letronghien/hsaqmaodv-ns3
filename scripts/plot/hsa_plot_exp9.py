#!/usr/bin/env python3
"""
EXP-9: Sparse FANET — N=5,8 — all 5 protocols
Run on server: python3 hsa_plot_exp9.py
Output: ~/H-SA-full-results/hsa-exp9-sparse.png
"""
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

CSV = '/home/tronghien1011/H-SA-full-results/exp9-sparse.csv'
OUT = '/home/tronghien1011/H-SA-full-results/hsa-exp9-sparse.png'

COLS = ['scenario','protocol','mob','mp','N','unk','vMin','vMax','pkt','T','seed',
        'PDR','delay','thr','rOver','E','extra']

df = pd.read_csv(CSV, header=None, names=COLS, on_bad_lines='skip')
for col in ['PDR','delay','thr','rOver','N']:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df = df.dropna(subset=['PDR'])

# ─── Print full stats table ───────────────────────────────────
print("=== FULL STATS (mean ± std, 30 seeds) ===")
for N in [5, 8]:
    sub = df[df['N']==N]
    print(f"\n--- N={N} ---")
    for proto in ['AODV','PMAODV','QMAODV','SAQMAODV','HSAQMAODV']:
        s = sub[sub['protocol']==proto]
        print(f"  {proto:12s}: PDR={s['PDR'].mean():.1f}±{s['PDR'].std():.1f}%  "
              f"delay={s['delay'].mean():.0f}±{s['delay'].std():.0f}ms  "
              f"OH={s['rOver'].mean():.0f}")

# Mann-Whitney: HSAQMAODV vs SAQMAODV
print("\n=== Mann-Whitney: HSAQMAODV vs SAQMAODV ===")
for N in [5, 8]:
    sub = df[df['N']==N]
    h = sub[sub['protocol']=='HSAQMAODV']['PDR']
    s = sub[sub['protocol']=='SAQMAODV']['PDR']
    _, p = stats.mannwhitneyu(h, s, alternative='two-sided')
    print(f"  N={N}: HSAQMAODV {h.mean():.1f}% vs SAQMAODV {s.mean():.1f}%  p={p:.3f}")

# ─── Plot ─────────────────────────────────────────────────────
PROTOS = ['AODV','PMAODV','QMAODV','SAQMAODV','HSAQMAODV']
LABELS = ['AODV','P-MAODV','Q-MAODV','SA-QMAODV','H-SAQMAODV\n(proposed)']
COLORS = ['#555555','#2166ac','#4dac26','#d6604d','#b2182b']
N_VALS = [5, 8]
METRICS = [
    ('PDR',   'Packet Delivery Ratio (%)',      True),
    ('delay', 'Avg End-to-End Delay (ms)',       False),
    ('rOver', 'Routing Overhead (pkts)',         False),
]

fig, axes = plt.subplots(len(METRICS), len(N_VALS), figsize=(12, 11))
x = np.arange(len(PROTOS))
W = 0.6

for col_i, N in enumerate(N_VALS):
    sub = df[df['N'] == N]
    for row_i, (metric, ylabel, higher_better) in enumerate(METRICS):
        ax = axes[row_i][col_i]
        means, errs = [], []
        for proto in PROTOS:
            vals = sub[sub['protocol']==proto][metric].dropna()
            means.append(vals.mean() if len(vals)>0 else 0)
            errs.append(vals.std() if len(vals)>0 else 0)

        bars = ax.bar(x, means, W, yerr=errs, capsize=4,
                      color=COLORS, alpha=0.85, edgecolor='black', linewidth=0.5)

        # Annotate value
        for bar, m in zip(bars, means):
            if m > 0:
                ax.text(bar.get_x()+bar.get_width()/2,
                        bar.get_height() + max(errs)*0.05,
                        f'{m:.1f}', ha='center', va='bottom', fontsize=8, fontweight='bold')

        # Highlight H-SAQMAODV
        bars[-1].set_edgecolor('#6b1a1a')
        bars[-1].set_linewidth(2.5)

        # p-value bracket: HSAQMAODV vs SAQMAODV (index 3 vs 4)
        h_vals = sub[sub['protocol']=='HSAQMAODV'][metric].dropna()
        s_vals = sub[sub['protocol']=='SAQMAODV'][metric].dropna()
        if len(h_vals)>5 and len(s_vals)>5:
            _, p = stats.mannwhitneyu(h_vals, s_vals, alternative='two-sided')
            sig = '***' if p<0.001 else ('**' if p<0.01 else ('*' if p<0.05 else 'ns'))
            y_top = max(means[3]+errs[3], means[4]+errs[4]) * 1.1
            ax.plot([3,3,4,4],[y_top*0.96,y_top,y_top,y_top*0.96],'k-',lw=1)
            ax.text(3.5, y_top*1.01, f'p={p:.3f} {sig}',
                    ha='center', va='bottom', fontsize=8, color='dimgray')

        ax.set_xticks(x)
        ax.set_xticklabels(LABELS, fontsize=8)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_title(f'N = {N} nodes (sparse FANET)', fontsize=11, fontweight='bold')
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)

fig.suptitle('EXP-9: Sparse FANET Performance — N=5 and N=8\n'
             '(Speed=20 m/s, E₀=30 J, Gauss-Markov, 30 seeds)',
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches='tight')
print(f'\nSaved: {OUT}')
