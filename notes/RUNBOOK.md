# RUNBOOK — H-SAQMAODV Experiments
> Hướng dẫn chạy kịch bản, lấy dữ liệu và vẽ biểu đồ

---

## 1. Chuẩn bị môi trường

```bash
# Kiểm tra NS-3 đã build chưa
EXEC=$(find ~/ns-allinone-3.40-hsaqmaodv/ns-3.40/build \
  -name "*fanet-sim*" -executable -type f | head -1)
echo $EXEC   # phải có output

# Smoke test nhanh
for proto in AODV SAQMAODV HSAQMAODV; do
  echo -n "$proto: "
  $EXEC --protocol=$proto --numNodes=15 --simTime=30 \
    --maxPaths=3 --seed=1 --csvFile=/tmp/smoke.csv 2>&1 | tail -1
done
```

---

## 2. Các kịch bản thí nghiệm

### Kịch bản A — Paper1 Standard (Gauss-Markov)

**Script:** `~/run-paper1-experiments.sh`  
**Mục đích:** So sánh 5 protocols trên các điều kiện FANET chuẩn

```bash
tmux new -s paper1
NS3_DIR=~/ns-allinone-3.40-hsaqmaodv/ns-3.40 \
FAMILIES="TVI N S E L" \
SEEDS=30 \
bash ~/run-paper1-experiments.sh
# Ctrl+B → D để detach
```

**Tham số chính:**
- simTime=200s (đổi thành 400s cho final run)
- mobility=GAUSS (Gauss-Markov)
- numNodes: 5,8,10,15,20,25,30
- speed: 5,10,15,20,25,30,50 m/s
- E0: 10,20,30,50 J
- pktInterval: 0.05–1.0 s
- TVI sweep: tviHigh=3,5,8,10,15 × tviLow=0,1,2

**Jobs parallel theo family (tránh VM đơ):**
| Family | Jobs |
|--------|------|
| TVI, E | 6 |
| L | 4 |
| N, S | 3 |

**Thời gian ước tính (8 cores, SEEDS=30):**
- FAMILIES="N S E": ~4 giờ
- FAMILIES="TVI L": ~1.5 giờ
- Full (TVI N S E L): ~6-8 giờ

**Dữ liệu output:**
```
~/results-paper1-<YYYYMMDD-HHMMSS>/
├── merged.csv          ← file dữ liệu chính
├── run.log             ← log chạy
└── jobs/
    └── job-*.csv       ← từng job riêng lẻ
```

---

### Kịch bản B — HQA-comparable (RWP)

**Script:** `~/run-hqa-params.sh`  
**Mục đích:** Chạy điều kiện gần giống HQA paper để so sánh xu hướng

```bash
tmux new -s hqa
SEEDS=10 bash ~/run-hqa-params.sh
```

**Tham số chính:**
- mobility=RWP (Random Waypoint)
- areaX=500, areaY=500 m
- numNodes: 10,20,30,40,50,70
- speed: 10–100 m/s (random)
- pktSize=127 bytes
- initialEnergy=1000 J
- simTime=300s

**Thời gian ước tính:** ~2-3 giờ (SEEDS=10)

**Dữ liệu output:**
```
~/results-hqa-params-<YYYYMMDD-HHMMSS>/
├── merged.csv
└── jobs/
```

---

### Kịch bản C — simTime dài (Final run)

```bash
tmux new -s final
NS3_DIR=~/ns-allinone-3.40-hsaqmaodv/ns-3.40 \
FAMILIES="N S E" \
SEEDS=30 \
bash ~/run-paper1-experiments.sh
# Lưu ý: sửa simTime=400 trong script trước khi chạy
```

**Sửa simTime:**
```bash
sed -i 's/simTime=200/simTime=400/g' ~/run-paper1-experiments.sh
# Thêm E0 thấp
sed -i 's/for E0 in 10 20 30 50/for E0 in 3 5 10 20 30 50/' ~/run-paper1-experiments.sh
```

---

## 3. Xử lý khi bị interrupt

```bash
# Merge CSV thủ công
JOB_DIR=$(ls -dt ~/results-*/jobs 2>/dev/null | head -1)
MERGED=$(dirname "$JOB_DIR")/merged.csv
FIRST=$(ls "$JOB_DIR"/*.csv 2>/dev/null | head -1)

if [ -n "$FIRST" ]; then
    head -1 "$FIRST" > "$MERGED"
    for f in "$JOB_DIR"/*.csv; do tail -n +2 "$f" >> "$MERGED"; done
    echo "Merged: $MERGED ($(wc -l < $MERGED) rows)"
else
    echo "Không có CSV nào"
fi
```

---

## 4. Vẽ biểu đồ

### Plot tất cả figures (Paper1)

```bash
# Tìm merged.csv mới nhất
MERGED=$(ls -t ~/results-paper1-*/merged.csv 2>/dev/null | head -1)
echo "Using: $MERGED"

# Vẽ
python3 ~/plot-paper1.py "$MERGED" --outdir ~/figures-out

# Kiểm tra output
ls ~/figures-out/
```

**Figures được tạo:**
| File | Nội dung |
|------|---------|
| `fig2_tvi_heatmap.pdf` | TVI threshold sensitivity (cần chạy TVI family) |
| `fig3_pdr_vs_n.pdf` | PDR vs Node Density |
| `fig4_pdr_vs_speed.pdf` | PDR vs Mobility Speed |
| `fig5_pdr_vs_energy.pdf` | PDR vs Battery Capacity |
| `fig_pdr_vs_load.pdf` | PDR vs Traffic Load |

**Lưu ý quan trọng:**
- TVI heatmap cần family TVI với scenario name dạng `TVI-N15-V20-T200-E0-H{high}-L{low}`
- Nếu skip TVI family → fig2 không có data
- Plot script đã fix: parse tviHigh/tviLow từ scenario name (không đọc từ CSV columns)

### Plot HQA params (custom)

```bash
# Xem phân bố data trước
python3 -c "
import csv
from collections import defaultdict
MERGED = sorted(__import__('glob').glob('/home/tronghien1011/results-hqa-params-*/merged.csv'))[-1]
rows = list(csv.DictReader(open(MERGED)))
agg = defaultdict(list)
for r in rows:
    agg[(r['protocol'], r['numNodes'])].append(float(r['deliveryRatio']))
print('Protocol     ', '  '.join(['N='+n for n in ['10','20','30','40','50','70']]))
for p in ['AODV','QMAODV','SAQMAODV','HSAQMAODV']:
    vals = ['{:.1f}%'.format(sum(agg.get((p,n),[0]))/max(1,len(agg.get((p,n),[])))) for n in ['10','20','30','40','50','70']]
    print('{:<12}'.format(p), '  '.join(vals))
"
```

---

## 5. Lấy dữ liệu về local

```bash
# Nén figures
cd ~ && zip figures-<version>.zip figures-out/*.pdf && echo "Done: ~/figures-<version>.zip"

# SCP về máy local (chạy trên máy local)
scp tronghien1011@<IP_VM>:~/figures-<version>.zip E:\CODE\H_SAQMAODV\

# Hoặc SCP merged.csv về để phân tích
scp tronghien1011@<IP_VM>:~/results-paper1-<timestamp>/merged.csv E:\CODE\H_SAQMAODV\data\
```

---

## 6. Push lên GitHub

```bash
cd ~/hsaqmaodv-ns3

# Sync code mới nhất
cp ~/ns-allinone-3.40-hsaqmaodv/ns-3.40/src/saqmaodv/model/saqmaodv-qtable.cc src/saqmaodv/model/
cp ~/ns-allinone-3.40-hsaqmaodv/ns-3.40/src/saqmaodv/model/saqmaodv-qtable.h src/saqmaodv/model/
cp ~/ns-allinone-3.40-hsaqmaodv/ns-3.40/src/saqmaodv/model/saqmaodv-routing-protocol.cc src/saqmaodv/model/
cp ~/ns-allinone-3.40-hsaqmaodv/ns-3.40/src/hsaqmaodv/model/hsaqmaodv-routing-protocol.cc src/hsaqmaodv/model/

# Sync scripts
cp ~/run-paper1-experiments.sh hsaqmaodv/scripts/run/
cp ~/run-hqa-params.sh hsaqmaodv/scripts/run/
cp ~/plot-paper1.py hsaqmaodv/scripts/plot/

# Commit và push
git add .
git commit -m "chore: sync scripts and code - <mô tả thay đổi>"
git push
```

---

## 7. Tmux cheat sheet

```bash
tmux new -s <name>          # Tạo session mới
tmux attach -t <name>       # Quay lại session
tmux ls                     # Liệt kê sessions
Ctrl+B → D                  # Detach (chạy nền)
Ctrl+B → [                  # Scroll mode (q để thoát)
```

---

## 8. Kiểm tra tiến độ đang chạy

```bash
# Xem log realtime
tail -f ~/results-paper1-*/run.log

# Đếm jobs hoàn thành
ls ~/results-paper1-*/jobs/*.csv 2>/dev/null | wc -l

# Load máy
uptime
htop  # hoặc top
```

---

## 9. Thứ tự chạy khuyến nghị (final)

```bash
# Bước 1: TVI sweep (nhẹ, ~30 phút)
NS3_DIR=~/ns-allinone-3.40-hsaqmaodv/ns-3.40 \
FAMILIES="TVI" SEEDS=10 bash ~/run-paper1-experiments.sh

# Bước 2: HQA params (parallel)
SEEDS=10 bash ~/run-hqa-params.sh

# Bước 3: Full paper1 (sau khi xác nhận TVI tốt)
NS3_DIR=~/ns-allinone-3.40-hsaqmaodv/ns-3.40 \
FAMILIES="N S E L" SEEDS=30 bash ~/run-paper1-experiments.sh

# Bước 4: Merge TVI + paper1 results rồi plot
cat ~/results-paper1-<tvi>/jobs/*.csv | grep -v "^scenario" >> ~/results-paper1-<main>/merged.csv
python3 ~/plot-paper1.py ~/results-paper1-<main>/merged.csv --outdir ~/figures-final
```
