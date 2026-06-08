# H-SAQMAODV Project Notes
> Ghi chú toàn bộ dự án — cập nhật lần cuối: 2026-06-04

---

## 1. Tổng quan dự án

**Tên:** H-SAQMAODV (Hybrid Self-Adaptive Q-learning Multipath AODV)  
**Mục tiêu:** Giao thức định tuyến FANET tự thích nghi với topology thông qua TVI-based 3-mode switching  
**NS-3 version:** 3.40  
**Thư mục NS-3 trên VM:** `~/ns-allinone-3.40-hsaqmaodv/ns-3.40/`  
**GitHub repo:** https://github.com/Letronghien/hsaqmaodv-ns3  
**VM user:** tronghien1011@ns3-research  

---

## 2. Chuỗi tiến hóa giao thức

```
AODV (NS-3 gốc)
└── PMAODV          — multipath, chọn theo hop count
    └── QMAODV      — Q-table, ε-greedy, reward = ACK + 1/(delay+1)
        └── SAQMAODV — 3 cơ chế self-adaptive
            └── HSAQMAODV — TVI 3-mode switching (đóng góp chính)
```

### SA-QMAODV (base)
- **Adaptive ε:** tăng +0.20 khi RERR, giảm -0.02 định kỳ
- **Adaptive α:** `α = 0.1 + 0.8*(1 - exp(-λ*ΔSeq))`
- **Adaptive weights:** normal (0.5,0.4,0.1) → low-energy (0.1,0.1,0.8) khi pin < 20%

### H-SAQMAODV — TVI Switching
```
TVI = ΔSeq_count / window_seconds

TVI > tviHigh  →  BYPASS:   greedy (ε=0), không explore
TVI < tviLow   →  GREEDY:   Q-value cao nhất (ε=0)  
otherwise      →  EXPLORE:  ε-greedy bình thường
```
**Default params (tuned từ heatmap):** `tviHigh=5, tviLow=2`

---

## 3. Cải tiến theo phiên bản

### v1 (ban đầu)
- TVI 3-mode switching cơ bản
- BYPASS = dùng primary route duy nhất (như AODV)

### v2
1. **Enhanced BYPASS:** greedy (ε=0) thay vì single path
2. **Congestion reward:** thêm `w4*(1-queueOcc)` vào reward function
3. **Hysteresis:** chỉ đổi mode sau N tick liên tiếp (N=3)
4. **Proportional ε bump:** bump tỉ lệ với error rate gần đây

### v3 (hiện tại — best)
5. **Void Detection:** `OnVoidDetected()` — bump ε mạnh khi không tìm được route cho destination đã biết
6. **AODV Dual Q-update:** `UpdateFromAODVRoute()` — dùng AODV path làm training sample với α/2 (inspired by HQA)
7. **Adaptive Hello:** thử 0.7/1.0/1.2s theo TVI → **reverted về 1.0s** (không có lợi ích nhất quán)

**TVI threshold tuning:** heatmap sweep cho thấy `tviHigh=5, tviLow=2` tốt nhất (PDR=34.8%)

---

## 4. Reward Function

```
r_t = w1*ACK + w2*(1/(delay+1)) + w3*E_res + w4*(1-queueOcc)
```

- w1=0.5 (ACK success)
- w2=0.4 (delay inverse)  
- w3=0.1 (energy fraction)
- w4=0.1 (congestion — 1 - queue occupancy)

**Low energy mode** (E_res < 20%): (w1,w2,w3,w4) = (0.1,0.1,0.8,0.0)

**Sigmoid energy weights** (H-SAQMAODV):
```
s = sigmoid((E - θ) / σ),  θ=0.30, σ=0.08
w3 = 0.10 + 0.70*s
w2 = 0.40*(1-s)
w1 = 1 - w2 - w3
```

---

## 5. Cấu trúc thư mục

### NS-3 source (VM)
```
~/ns-allinone-3.40-hsaqmaodv/ns-3.40/src/
├── saqmaodv/model/
│   ├── saqmaodv-qtable.h          # QTable class với tất cả cải tiến
│   ├── saqmaodv-qtable.cc         # Implementation
│   ├── saqmaodv-routing-protocol.h
│   └── saqmaodv-routing-protocol.cc
├── hsaqmaodv/model/
│   ├── hsaqmaodv-qtable.h         # Kế thừa từ saqmaodv::QTable
│   ├── hsaqmaodv-qtable.cc
│   ├── hsaqmaodv-routing-protocol.h
│   └── hsaqmaodv-routing-protocol.cc
├── qmaodv/model/                  # QMAODV base
└── pmaodv/model/                  # PMAODV base
```

### GitHub repo
```
hsaqmaodv-ns3/
├── src/
│   ├── saqmaodv/model/            # Core files (synced từ VM)
│   └── hsaqmaodv/model/
├── hsaqmaodv/
│   ├── scripts/
│   │   ├── run/
│   │   │   └── run-paper1-experiments.sh
│   │   └── plot/
│   │       └── plot-paper1.py
│   └── patches/
├── notes/
├── results/
└── PAPER-OUTLINE.md
```

### Scripts trên VM
```
~/run-paper1-experiments.sh     # Script chạy experiments chính
~/run-hqa-params.sh             # Script chạy với HQA parameters
~/plot-paper1.py                # Script vẽ biểu đồ
~/patch-hsaqmaodv-v2.py         # Patch script v2
~/patch-hsaqmaodv-v3.py         # Patch script v3
```

---

## 6. Build instructions

```bash
# Build NS-3
cmake --build ~/ns-allinone-3.40-hsaqmaodv/ns-3.40/cmake-cache -j$(nproc)

# Kiểm tra lỗi
cmake --build ~/ns-allinone-3.40-hsaqmaodv/ns-3.40/cmake-cache -j$(nproc) \
  2>&1 | grep "error:" | head -10

# Smoke test
EXEC=$(find ~/ns-allinone-3.40-hsaqmaodv/ns-3.40/build -name "*fanet-sim*" \
  -executable -type f | head -1)
for proto in AODV QMAODV SAQMAODV HSAQMAODV; do
  echo -n "$proto: "
  $EXEC --protocol=$proto --numNodes=15 --simTime=30 \
    --maxPaths=3 --seed=1 --csvFile=/tmp/smoke.csv 2>&1 | tail -1
done
```

---

## 7. Experiment Parameters

### Bộ tham số chuẩn (paper1)
```bash
NS3_DIR=~/ns-allinone-3.40-hsaqmaodv/ns-3.40
FAMILIES="TVI N S E L"
SEEDS=30
JOBS=$(nproc)
bash ~/run-paper1-experiments.sh
```

**Simulation settings:**
- simTime=200s (→ 400s cho final)
- numNodes: 5,8,10,15,20,25,30
- speed: 5,10,15,20,25,30,50 m/s
- E0: 10,20,30,50 J (→ thêm 3,5 J cho final)
- pktInterval: 0.05-1.0 s
- mobility: GAUSS (Gauss-Markov)
- maxPaths=3, pktSize=512

**TVI family sweep:**
- tviHigh: 3,5,8,10,15
- tviLow: 0,1,2
- Best: tviHigh=5, tviLow=2 (PDR=34.8%)

### Bộ tham số HQA-comparable
```bash
SEEDS=10 bash ~/run-hqa-params.sh
```
- mobility=RWP
- areaX=500, areaY=500
- numNodes: 10,20,30,40,50,70
- speed: 10-100 m/s (random)
- pktSize=127 bytes
- initialEnergy=1000 J
- simTime=300s

---

## 8. Kết quả tóm tắt (v3, SEEDS=30)

### Paper params (Gauss-Markov, simTime=200)
| Family | H-SAQMAODV vs AODV | Nhận xét |
|--------|-------------------|---------|
| N=5-15 | Cạnh tranh | Q-learning bắt đầu học |
| Speed=20-50 | +3-5% PDR | BYPASS+dual update hiệu quả |
| Energy (all) | **+3% nhất quán** | Sigmoid weights hoạt động |
| N>20 | ≈ AODV | Congestion dominant |
| Speed=5 | ≈ AODV | TVI thấp → GREEDY mode |

**Delay improvement (tviHigh=5):** HSAQMAODV 161ms vs AODV 438ms (-63%)

### HQA params (RWP, N=10-20 partial)
| Protocol | N=10 | N=20 | Xu hướng |
|----------|------|------|---------|
| AODV | 95.8% | 89.6% | ↓ giảm |
| HSAQMAODV | 89.0% | **91.0%** | ↑ tăng theo N |
| SAQMAODV | 90.4% | **91.2%** | ↑ tăng theo N |

Q-learning protocols overtake AODV khi N tăng — cần chạy đến N=70 để xác nhận.

---

## 9. Key Commands

```bash
# Chạy experiments
tmux new -s paper1
NS3_DIR=~/ns-allinone-3.40-hsaqmaodv/ns-3.40 \
FAMILIES="N S E" SEEDS=30 JOBS=$(nproc) \
bash ~/run-paper1-experiments.sh

# Vẽ biểu đồ
python3 ~/plot-paper1.py ~/results-paper1-<timestamp>/merged.csv \
  --outdir ~/figures-out

# Nén để tải về
cd ~ && zip figures.zip figures-out/*.pdf

# Tải về local (chạy trên máy local)
scp tronghien1011@<IP_VM>:~/figures.zip E:\CODE\H_SAQMAODV\

# Push code lên GitHub
cd ~/hsaqmaodv-ns3
cp ~/ns-allinone-3.40-hsaqmaodv/ns-3.40/src/saqmaodv/model/saqmaodv-qtable.cc src/saqmaodv/model/
cp ~/ns-allinone-3.40-hsaqmaodv/ns-3.40/src/saqmaodv/model/saqmaodv-qtable.h src/saqmaodv/model/
cp ~/ns-allinone-3.40-hsaqmaodv/ns-3.40/src/saqmaodv/model/saqmaodv-routing-protocol.cc src/saqmaodv/model/
cp ~/ns-allinone-3.40-hsaqmaodv/ns-3.40/src/hsaqmaodv/model/hsaqmaodv-routing-protocol.cc src/hsaqmaodv/model/
git add src/ && git commit -m "..." && git push

# Merge CSV thủ công (khi bị interrupt)
JOB_DIR=$(ls -dt ~/results-*/jobs 2>/dev/null | head -1)
MERGED=$(dirname "$JOB_DIR")/merged.csv
FIRST=$(ls "$JOB_DIR"/*.csv | head -1)
head -1 "$FIRST" > "$MERGED"
for f in "$JOB_DIR"/*.csv; do tail -n +2 "$f" >> "$MERGED"; done
```

---

## 10. Known Issues & Fixes

| Issue | Fix |
|-------|-----|
| `UpdateQValueOrCreate` type mismatch (hsaqmaodv::RoutingTableEntry) | Giữ 4-arg signature, queueOcc=0.0 internally |
| TVI heatmap colorbar ×100 | `imshow(matrix)` không ×100, fix vmin/vmax |
| TVI heatmap 1 data point | Encode `-H{high}-L{low}` vào scenario name |
| OnVoidDetected fires too often | Chỉ gọi khi `CountFor(dst) > 0` |
| Adaptive hello 2.0s gây regression | Revert về 1.0s cố định |
| `IndentationError` line 15 trong Python summary | Bug nhỏ trong run script, không ảnh hưởng data |

---

## 11. Paper Strategy

**Target venue:** IEEE Access (Q2) hoặc Ad Hoc Networks (Q2/Q3)

**Narrative:** H-SAQMAODV đạt kết quả tương đương HQA (Q1) với overhead thấp hơn nhờ TVI O(1) thay vì Bayesian evaluation.

**Key arguments:**
- Lightweight: TVI = ΔSeq/window, O(1) per packet
- Adaptive: 3-mode switching vs binary switching của HQA
- Energy-aware: sigmoid weight adaptation
- Consistent delay improvement: -63% vs AODV

**Baselines needed:** AODV, PMAODV, QMAODV, SAQMAODV (có sẵn)
**Optional:** HQA re-implementation (nếu có full text và thời gian)

---

## 12. TODO (theo thứ tự ưu tiên)

- [ ] Chạy HQA params đầy đủ N=10-70 (SEEDS=10)
- [ ] Chạy final paper1 SEEDS=30, simTime=400s, thêm E0=3-5J
- [ ] Vẽ delay và throughput figures (đang thiếu)
- [ ] Tính p-value / confidence interval cho statistical significance
- [ ] Viết paper draft
- [ ] (Optional) Re-implement HQA để so sánh trực tiếp

---

## 13. Related Work

**HQA** (Chen Sun et al., Vehicular Communications 2025, Q1, IF=6.5)
- Bayesian stability evaluator cho adaptive Q-learning/AODV switching
- Dual-update reward: AODV paths làm Q-learning training samples
- Tool: không phải NS-3 (custom simulator)
- Params: RWP, N=10-70, speed=10-100, E0=1000J, area=500-1000m²
- Results: +5.4-9.1% PDR vs AODV, -13.6-23.9% delay
- **Không nên so sánh trực tiếp** do khác simulation tool

**Cite như related work:**
> "While HQA employs a Bayesian stability evaluator requiring per-packet posterior computation, H-SAQMAODV achieves comparable switching behavior through the lightweight TVI metric (O(1) overhead) with additional energy-awareness via sigmoid weight adaptation."
