#!/usr/bin/env python3
"""
patch-plot-delay.py
Thêm 2 hàm plot delay + throughput vào plot-paper1.py trên VM.
Chạy:  python3 ~/patch-plot-delay.py
"""
import re, os

PLOT_PATH = os.path.expanduser("~/plot-paper1.py")

# ── Code mới cần thêm ─────────────────────────────────────────────────────────
NEW_FUNCS = '''

# ─────────────────────────────────────────────────────────────────────────────
# FIG 6: Average End-to-End Delay vs Mobility Speed (Family S)
# ─────────────────────────────────────────────────────────────────────────────
def plot_delay_vs_speed(df, outdir):
    """Fig 6: avgDelay vs speed for Family S."""
    delay_col = None
    for c in ['avgDelay', 'avg_delay', 'delay', 'endToEndDelay', 'e2eDelay']:
        if c in df.columns:
            delay_col = c
            break
    if delay_col is None:
        print("[WARN] No delay column found in CSV — skipping fig6_delay_vs_speed")
        return

    sub = df[df['scenario'].str.startswith('S-')].copy()
    if sub.empty:
        print("[WARN] No Family-S data — skipping fig6_delay_vs_speed")
        return

    # Extract speed
    sub['speed'] = sub['scenario'].str.extract(r'S-N\\d+-V(\\d+)').astype(float)
    sub = sub.dropna(subset=['speed', delay_col])
    sub[delay_col] = pd.to_numeric(sub[delay_col], errors='coerce')

    agg = sub.groupby(['protocol','speed'])[delay_col].agg(['mean','std']).reset_index()

    fig, ax = plt.subplots(figsize=(7,4.5))
    for proto, style in PROTO_STYLES.items():
        d = agg[agg['protocol']==proto].sort_values('speed')
        if d.empty:
            continue
        ax.errorbar(d['speed'], d['mean'], yerr=d['std'],
                    label=style['label'], color=style['color'],
                    marker=style['marker'], linestyle=style['ls'],
                    capsize=4, linewidth=1.8)

    ax.set_xlabel("Mean Speed (m/s)", fontsize=12)
    ax.set_ylabel("Avg End-to-End Delay (ms)", fontsize=12)
    ax.set_title("Fig 6: Avg Delay vs Mobility Speed", fontsize=13)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.4)
    fig.tight_layout()
    out = os.path.join(outdir, "fig6_delay_vs_speed.pdf")
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Saved: {out}")


# ─────────────────────────────────────────────────────────────────────────────
# FIG 7: Throughput vs Node Density (Family N)
# ─────────────────────────────────────────────────────────────────────────────
def plot_throughput_vs_n(df, outdir):
    """Fig 7: throughput vs numNodes for Family N."""
    tput_col = None
    for c in ['throughput', 'avgThroughput', 'rxBytes', 'goodput']:
        if c in df.columns:
            tput_col = c
            break
    if tput_col is None:
        print("[WARN] No throughput column found — skipping fig7_throughput_vs_n")
        return

    sub = df[df['scenario'].str.startswith('N-')].copy()
    if sub.empty:
        print("[WARN] No Family-N data — skipping fig7_throughput_vs_n")
        return

    sub['numNodes'] = sub['scenario'].str.extract(r'N-N(\\d+)').astype(float)
    sub = sub.dropna(subset=['numNodes', tput_col])
    sub[tput_col] = pd.to_numeric(sub[tput_col], errors='coerce')

    agg = sub.groupby(['protocol','numNodes'])[tput_col].agg(['mean','std']).reset_index()

    fig, ax = plt.subplots(figsize=(7,4.5))
    for proto, style in PROTO_STYLES.items():
        d = agg[agg['protocol']==proto].sort_values('numNodes')
        if d.empty:
            continue
        ax.errorbar(d['numNodes'], d['mean'], yerr=d['std'],
                    label=style['label'], color=style['color'],
                    marker=style['marker'], linestyle=style['ls'],
                    capsize=4, linewidth=1.8)

    ax.set_xlabel("Number of Nodes", fontsize=12)
    ax.set_ylabel("Throughput (kbps)", fontsize=12)
    ax.set_title("Fig 7: Throughput vs Node Density", fontsize=13)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.4)
    fig.tight_layout()
    out = os.path.join(outdir, "fig7_throughput_vs_n.pdf")
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Saved: {out}")

'''

# ── Thêm gọi hàm vào main() ───────────────────────────────────────────────────
CALL_SNIPPET = """    plot_delay_vs_speed(df, outdir)
    plot_throughput_vs_n(df, outdir)
"""

def patch():
    with open(PLOT_PATH, 'r') as f:
        src = f.read()

    # Kiểm tra đã patch chưa
    if 'plot_delay_vs_speed' in src:
        print("Already patched — skip.")
        return

    # 1. Thêm hàm mới trước dòng "if __name__"
    if 'if __name__' in src:
        src = src.replace('if __name__', NEW_FUNCS + '\nif __name__')
    else:
        src += NEW_FUNCS

    # 2. Thêm lời gọi vào cuối main() — trước dòng print("Done") hoặc cuối hàm
    for marker in ['print("Done")', "print('Done')", 'plt.show()', 'print(f"All figures']:
        if marker in src:
            src = src.replace(marker, CALL_SNIPPET + '    ' + marker, 1)
            break
    else:
        # fallback: thêm cuối main block
        src = src.replace('\nif __name__', '\n' + CALL_SNIPPET + '\nif __name__')

    with open(PLOT_PATH, 'w') as f:
        f.write(src)
    print(f"Patched: {PLOT_PATH}")
    print("New functions added: plot_delay_vs_speed, plot_throughput_vs_n")

if __name__ == '__main__':
    patch()
