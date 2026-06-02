#!/usr/bin/env python3
"""
fix-hsaqmaodv-all.py
Chay tu thu muc project:  cd ~/hsaqmaodv-ns3 && python3 fix-hsaqmaodv-all.py

Sua 2 van de tu build error:
  1. Doi ten class SaqmaodvHelper -> HsaqmaodvHelper trong hsaqmaodv module
  2. Inject HSAQMAODV protocol block vao fanet-sim.cc (anchor da duoc sua)
"""
import os, re, sys
from pathlib import Path

NS3 = Path(os.environ.get("NS3_DIR", Path.home() / "ns-allinone-3.40/ns-3.40"))
HSA = NS3 / "src" / "hsaqmaodv"
FANET = NS3 / "scratch" / "fanet-sim.cc"

# ============================================================
# FIX 1: Doi ten class SaqmaodvHelper -> HsaqmaodvHelper
# ============================================================
print("=== FIX 1: Doi ten SaqmaodvHelper -> HsaqmaodvHelper ===")
if not HSA.exists():
    print(f"ERROR: {HSA} khong ton tai"); sys.exit(1)

renamed = 0
for ext in ("*.h", "*.cc"):
    for p in HSA.rglob(ext):
        txt = p.read_text(encoding="utf-8")
        new = re.sub(r"\bSaqmaodvHelper\b", "HsaqmaodvHelper", txt)
        if new != txt:
            p.write_text(new, encoding="utf-8")
            renamed += 1
            print(f"  renamed: {p.relative_to(NS3)}")

print(f"  Tong: {renamed} files da doi ten")

# ============================================================
# FIX 2: Patch fanet-sim.cc voi anchor dung
# ============================================================
print("\n=== FIX 2: Patch fanet-sim.cc ===")
if not FANET.exists():
    print(f"ERROR: {FANET} khong ton tai"); sys.exit(1)

bak = FANET.with_suffix(".cc.bak2.hsaqmaodv")
if not bak.exists():
    import shutil; shutil.copy(FANET, bak)
    print(f"  backup: {bak.name}")

txt = FANET.read_text(encoding="utf-8")
orig = txt
done = []

# 2a. Protocol help string
if "HSAQMAODV" not in txt:
    txt = txt.replace(
        '"Routing protocol (AODV|DSDV|DSR|PMAODV|AOMDV|QMAODV|SAQMAODV)"',
        '"Routing protocol (AODV|DSDV|DSR|PMAODV|AOMDV|QMAODV|SAQMAODV|HSAQMAODV)"', 1)
    done.append("protocol help string")

# 2b. TVI variable declarations
if "hsaTVIHigh" not in txt:
    anchor = "double      saAdaptPeriod = 10.0;"
    if anchor in txt:
        txt = txt.replace(anchor,
            anchor +
            "\n  double      hsaTVIHigh    = 3.0;      // H-SAQMAODV TVI upper threshold"
            "\n  double      hsaTVILow     = 1.0;      // H-SAQMAODV TVI lower threshold", 1)
        done.append("TVI var declarations")

# 2c. CLI args -- ANCHOR CORRETTO: ngoac khong co space
if '"hsaTVIHigh"' not in txt:
    # Anchor thuc te: cmd.AddValue("saW3",  (khong co space)
    anchor = 'cmd.AddValue("saW3",'
    idx = txt.find(anchor)
    if idx >= 0:
        end = txt.find(";", idx)
        txt = txt[:end+1] + (
            "\n  cmd.AddValue(\"hsaTVIHigh\", \"H-SAQMAODV TVI upper (BYPASS above)\", hsaTVIHigh);"
            "\n  cmd.AddValue(\"hsaTVILow\",  \"H-SAQMAODV TVI lower (GREEDY below)\", hsaTVILow);"
        ) + txt[end+1:]
        done.append("CLI args hsaTVIHigh/hsaTVILow")
    else:
        print("  WARN: anchor cmd.AddValue(\"saW3\" khong tim thay")

# 2d. HSAQMAODV routing block
# Anchor thuc te: "} else /* SAQMAODV */ {"
if 'protocol == "HSAQMAODV"' not in txt:
    anchor = "} else /* SAQMAODV */ {"
    if anchor in txt:
        hsaq_block = (
            "} else if (protocol == \"HSAQMAODV\") {\n"
            "      HsaqmaodvHelper hsaqmaodv;\n"
            "      hsaqmaodv.SetTVIThresholds(hsaTVIHigh, hsaTVILow);\n"
            "      hsaqmaodv.Set(\"MaxPaths\",              UintegerValue(maxPaths));\n"
            "      hsaqmaodv.Set(\"Alpha0\",                DoubleValue(saAlpha0));\n"
            "      hsaqmaodv.Set(\"Gamma\",                 DoubleValue(saGamma));\n"
            "      hsaqmaodv.Set(\"Epsilon0\",              DoubleValue(saEpsilon0));\n"
            "      hsaqmaodv.Set(\"RewardW1\",              DoubleValue(saW1));\n"
            "      hsaqmaodv.Set(\"RewardW2\",              DoubleValue(saW2));\n"
            "      hsaqmaodv.Set(\"RewardW3\",              DoubleValue(saW3));\n"
            "      hsaqmaodv.Set(\"Lambda\",                DoubleValue(saLambda));\n"
            "      hsaqmaodv.Set(\"SeqNoWindow\",           TimeValue(Seconds(saSeqNoWin)));\n"
            "      hsaqmaodv.Set(\"LowEnergyThreshold\",    DoubleValue(saLowEThresh));\n"
            "      hsaqmaodv.Set(\"PeriodicAdaptInterval\", TimeValue(Seconds(saAdaptPeriod)));\n"
            "      internet.SetRoutingHelper(hsaqmaodv);\n"
            "    "
        )
        txt = txt.replace(anchor, hsaq_block + anchor, 1)
        done.append("HSAQMAODV routing block")
    else:
        print("  WARN: anchor \"} else /* SAQMAODV */ {\" khong tim thay")

# 2e. maxPaths / CSV conditions
OLD = '|| protocol == "SAQMAODV"'
NEW = '|| protocol == "SAQMAODV" || protocol == "HSAQMAODV"'
if OLD in txt:
    n = txt.count(OLD); txt = txt.replace(OLD, NEW)
    done.append(f"maxPaths/CSV conditions ({n}x)")

# 2f. console print cho HSAQMAODV
if 'protocol == "HSAQMAODV"' in txt and "hsaTVIHigh" not in txt.split('protocol == "HSAQMAODV"')[1][:200]:
    anchor = 'if (protocol == "SAQMAODV")\n    std::cout'
    if anchor in txt:
        inject = (
            "if (protocol == \"HSAQMAODV\")\n"
            "    std::cout << \"(TVIHigh=\" << hsaTVIHigh << \" TVILow=\" << hsaTVILow << \")\";"
            "\n  "
        )
        txt = txt.replace(anchor, inject + anchor, 1)
        done.append("HSAQMAODV console print")

if txt != orig:
    FANET.write_text(txt, encoding="utf-8")
    for d in done: print(f"  + {d}")
else:
    print("  Khong co thay doi (da patch truoc do?)")

print()
print("=== XONG ===")
print("Rebuild:")
print(f"  cd {NS3} && ./ns3 build 2>&1 | tail -20")
print("Test:")
print("  ./ns3 run \'fanet-sim --protocol=HSAQMAODV --numNodes=10 --simTime=30\'")
