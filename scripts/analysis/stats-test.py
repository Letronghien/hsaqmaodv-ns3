#!/usr/bin/env python3
"""
stats-test.py  --  Wilcoxon signed-rank test for H-SAQMAODV paper
Usage:  python3 ~/stats-test.py <merged.csv>
Output: p-values table (console) + stats-results.csv
"""
import sys, csv, re
from collections import defaultdict
from scipy.stats import wilcoxon
import numpy as np

PROPOSED = "HSAQMAODV"
BASELINES = ["AODV", "PMAODV", "QMAODV", "SAQMAODV"]

def load(path):
    rows = list(csv.DictReader(open(path)))
    return rows

def family_key(scenario):
    """Return (family, x_value) from scenario name."""
    # TVI family: TVI-N15-V20-T200-E30-H5-L2
    if scenario.startswith("TVI"):
        return None  # skip TVI for stats

    # Speed family: S-N15-V{speed}-T200-E30
    m = re.match(r'S-N\d+-V(\d+)', scenario)
    if m:
        return ('speed', int(m.group(1)))

    # Node family: N-N{n}-V20-T200-E30
    m = re.match(r'N-N(\d+)-V', scenario)
    if m:
        return ('nodes', int(m.group(1)))

    # Energy family: E-N15-V20-T200-E{e0}
    m = re.match(r'E-N\d+-V\d+-T\d+-E(\d+)', scenario)
    if m:
        return ('energy', int(m.group(1)))

    # Load family: L-N15-V20-T200-E30-I{interval}
    m = re.match(r'L-N\d+-V\d+-T\d+-E\d+-I([\d.]+)', scenario)
    if m:
        return ('load', float(m.group(1)))

    return None

def aggregate(rows):
    """Build dict: (family, x_val, protocol) -> list of PDR values."""
    data = defaultdict(list)
    for r in rows:
        fk = family_key(r.get('scenario',''))
        if fk is None:
            continue
        family, x = fk
        proto = r.get('protocol','')
        try:
            pdr = float(r['deliveryRatio'])
        except (KeyError, ValueError):
            continue
        data[(family, x, proto)].append(pdr)
    return data

def run_tests(data):
    families = ['speed', 'nodes', 'energy', 'load']
    results = []
    print(f"\n{'='*70}")
    print(f"Wilcoxon Signed-Rank Test: H-SAQMAODV vs Baselines")
    print(f"{'='*70}")

    for family in families:
        xs = sorted(set(x for (f,x,p) in data if f==family))
        print(f"\n--- Family: {family.upper()} ---")
        print(f"{'Baseline':<14} {'x':<8} {'n':<5} {'HSAQ mean':<12} {'Base mean':<12} {'p-value':<12} {'sig'}")
        print("-"*70)

        for baseline in BASELINES:
            for x in xs:
                h = data.get((family, x, PROPOSED), [])
                b = data.get((family, x, baseline), [])
                n = min(len(h), len(b))
                if n < 5:
                    continue
                h_trim = h[:n]
                b_trim = b[:n]
                diff = [hi - bi for hi, bi in zip(h_trim, b_trim)]
                if all(d == 0 for d in diff):
                    p = 1.0
                else:
                    try:
                        _, p = wilcoxon(h_trim, b_trim, alternative='greater')
                    except Exception:
                        p = float('nan')
                sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
                h_mean = np.mean(h_trim)
                b_mean = np.mean(b_trim)
                print(f"{baseline:<14} {str(x):<8} {n:<5} {h_mean:<12.2f} {b_mean:<12.2f} {p:<12.4f} {sig}")
                results.append({
                    'family': family, 'x': x, 'baseline': baseline,
                    'n': n, 'hsaq_mean': round(h_mean,3),
                    'base_mean': round(b_mean,3), 'p_value': round(p,6),
                    'significant': sig
                })
    return results

def summary_table(results):
    """Print a clean summary: for each family, count how many x-points are significant."""
    print(f"\n{'='*70}")
    print("SUMMARY: Significant improvements (p<0.05) by family")
    print(f"{'='*70}")
    for family in ['speed','nodes','energy','load']:
        frows = [r for r in results if r['family']==family]
        for baseline in BASELINES:
            brows = [r for r in frows if r['baseline']==baseline]
            sig = sum(1 for r in brows if r['significant'] != 'ns')
            total = len(brows)
            pct = 100*sig/total if total else 0
            print(f"  {family:<8} vs {baseline:<12}: {sig}/{total} x-points significant ({pct:.0f}%)")

def main():
    path = sys.argv[1] if len(sys.argv)>1 else None
    if not path:
        # Try to find latest merged.csv
        import glob
        files = sorted(glob.glob(
            '/home/tronghien1011/results-paper1-*/merged.csv'))
        if not files:
            print("Usage: python3 stats-test.py <merged.csv>")
            sys.exit(1)
        path = files[-1]
        print(f"Auto-detected: {path}")

    rows = load(path)
    print(f"Loaded {len(rows)} rows from {path}")
    data = aggregate(rows)
    results = run_tests(data)
    summary_table(results)

    # Save CSV
    out = path.replace('merged.csv','stats-results.csv')
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['family','x','baseline','n',
                                           'hsaq_mean','base_mean','p_value','significant'])
        w.writeheader()
        w.writerows(results)
    print(f"\nSaved: {out}")

if __name__ == '__main__':
    main()
