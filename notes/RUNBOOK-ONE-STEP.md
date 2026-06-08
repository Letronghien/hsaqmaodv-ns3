# RUNBOOK ONE-STEP — H-SAQMAODV
> Chạy từng kịch bản độc lập, xong tự vẽ. Nếu đơ chỉ mất 1 kịch bản.

---

## Cài đặt một lần (copy lên VM)

```bash
# Copy 2 scripts lên VM
scp run-one-family.sh tronghien1011@<IP_VM>:~/
scp run-all-families.sh tronghien1011@<IP_VM>:~/
chmod +x ~/run-one-family.sh ~/run-all-families.sh
```

---

## Script run-one-family.sh

```bash
#!/bin/bash
# Usage: bash run-one-family.sh <FAMILY> <SEEDS>

FAMILY=$1
SEEDS=${2:-10}
NS3_DIR=~/ns-allinone-3.40-hsaqmaodv/ns-3.40

echo "=== Family: $FAMILY | Seeds: $SEEDS ==="

NS3_DIR=$NS3_DIR FAMILIES="$FAMILY" SEEDS=$SEEDS \
  bash ~/run-paper1-experiments.sh

MERGED=$(ls -t ~/results-paper1-*/merged.csv 2>/dev/null | head -1)
[ -z "$MERGED" ] && echo "Không có merged.csv" && exit 1

OUTDIR=~/figures-${FAMILY}-$(date +%H%M%S)
python3 ~/plot-paper1.py "$MERGED" --outdir "$OUTDIR"

zip ~/figures-${FAMILY}.zip "$OUTDIR"/*.pdf 2>/dev/null && \
  echo "Done: ~/figures-${FAMILY}.zip" || echo "Không có PDF"
```

---

## Kịch bản 1 — TVI Threshold Sensitivity

**Mục đích:** Tìm tviHigh/tviLow tốt nhất → heatmap  
**Nặng/nhẹ:** Nhẹ (~20 phút)  
**Chạy:**
```bash
tmux new -s fam-tvi
bash ~/run-one-family.sh TVI 10
```
**Output:** `~/figures-TVI.zip` → `fig2_tvi_heatmap.pdf`  
**Best params từ kết quả:** tviHigh=5, tviLow=2

---

## Kịch bản 2 — PDR vs Node Density (N)

**Mục đích:** Xem H-SAQMAODV vs các protocol khi mật độ node thay đổi  
**Nặng/nhẹ:** Nặng (~2-3 giờ, SEEDS=30)  
**Chạy:**
```bash
tmux new -s fam-n
bash ~/run-one-family.sh N 30
```
**Output:** `~/figures-N.zip` → `fig3_pdr_vs_n.pdf`  
**Parallel jobs:** 3 (tự động trong script)

---

## Kịch bản 3 — PDR vs Mobility Speed (S)

**Mục đích:** Đánh giá robustness khi tốc độ UAV thay đổi  
**Nặng/nhẹ:** Nặng (~2-3 giờ, SEEDS=30)  
**Chạy:**
```bash
tmux new -s fam-s
bash ~/run-one-family.sh S 30
```
**Output:** `~/figures-S.zip` → `fig4_pdr_vs_speed.pdf`  
**Parallel jobs:** 3

---

## Kịch bản 4 — PDR vs Battery (E)

**Mục đích:** Đánh giá energy-awareness của H-SAQMAODV  
**Nặng/nhẹ:** Nhẹ (~1 giờ, SEEDS=30)  
**Chạy:**
```bash
tmux new -s fam-e
bash ~/run-one-family.sh E 30
```
**Output:** `~/figures-E.zip` → `fig5_pdr_vs_energy.pdf`  
**Parallel jobs:** 6  
**Lưu ý:** Thêm E0=3,5J để thấy rõ energy advantage:
```bash
sed -i 's/for E0 in 10 20 30 50/for E0 in 3 5 10 20 30 50/' ~/run-paper1-experiments.sh
```

---

## Kịch bản 5 — PDR vs Traffic Load (L)

**Mục đích:** Đánh giá khi tải mạng thay đổi  
**Nặng/nhẹ:** Trung bình (~1.5 giờ, SEEDS=30)  
**Chạy:**
```bash
tmux new -s fam-l
bash ~/run-one-family.sh L 30
```
**Output:** `~/figures-L.zip` → `fig_pdr_vs_load.pdf`  
**Parallel jobs:** 4

---

## Kịch bản 6 — HQA-comparable Params

**Mục đích:** So sánh xu hướng với điều kiện giống HQA paper  
**Nặng/nhẹ:** Trung bình (~2 giờ, SEEDS=10)  
**Chạy:**
```bash
tmux new -s hqa
SEEDS=10 bash ~/run-hqa-params.sh
```
**Output:** `~/results-hqa-params-<timestamp>/merged.csv`  
**Vẽ thủ công sau:**
```bash
# Merge nếu bị interrupt
JOB_DIR=$(ls -dt ~/results-hqa-params-*/jobs | head -1)
MERGED=$(dirname "$JOB_DIR")/merged.csv
FIRST=$(ls "$JOB_DIR"/*.csv | head -1)
head -1 "$FIRST" > "$MERGED"
for f in "$JOB_DIR"/*.csv; do tail -n +2 "$f" >> "$MERGED"; done

# Phân tích nhanh
python3 -c "
import csv
from collections import defaultdict
rows = list(csv.DictReader(open('$MERGED')))
agg = defaultdict(list)
for r in rows:
    agg[(r['protocol'], r['numNodes'])].append(float(r['deliveryRatio']))
print('Protocol     N=10   N=20   N=30   N=40   N=50   N=70')
for p in ['AODV','QMAODV','SAQMAODV','HSAQMAODV']:
    vals = ['{:.1f}%'.format(sum(agg.get((p,n),[0]))/max(1,len(agg.get((p,n),[])))) for n in ['10','20','30','40','50','70']]
    print('{:<12}'.format(p), '  '.join(vals))
"
```

---

## Kịch bản 7 — simTime dài (Final)

**Mục đích:** Kết quả cuối cùng để viết paper, Q-learning đủ thời gian converge  
**Nặng/nhẹ:** Rất nặng (~8-10 giờ, SEEDS=30, simTime=400)  
**Chuẩn bị:**
```bash
# Sửa simTime trước khi chạy
sed -i 's/simTime=200/simTime=400/g' ~/run-paper1-experiments.sh
# Kiểm tra
grep "simTime" ~/run-paper1-experiments.sh | head -3
```
**Chạy từng family:**
```bash
tmux new -s final-n
bash ~/run-one-family.sh N 30

tmux new -s final-s
bash ~/run-one-family.sh S 30

tmux new -s final-e
bash ~/run-one-family.sh E 30
```
**Sau khi xong, restore simTime=200:**
```bash
sed -i 's/simTime=400/simTime=200/g' ~/run-paper1-experiments.sh
```

---

## Chạy tất cả cùng lúc (nếu VM ổn định)

```bash
bash ~/run-all-families.sh 30
# Xem tiến độ
tmux ls
tmux attach -t fam-<name>
```

---

## Gộp nhiều kết quả thành 1 file để vẽ tổng

```bash
# Gộp nhiều merged.csv từ các family riêng lẻ
OUTPUT=~/merged-all-$(date +%Y%m%d).csv

# Header từ file đầu tiên
FIRST=$(ls ~/results-paper1-*/merged.csv 2>/dev/null | head -1)
head -1 "$FIRST" > "$OUTPUT"

# Append data từ tất cả
for f in ~/results-paper1-*/merged.csv; do
  tail -n +2 "$f" >> "$OUTPUT"
done

echo "Total rows: $(wc -l < $OUTPUT)"

# Vẽ tổng hợp
python3 ~/plot-paper1.py "$OUTPUT" --outdir ~/figures-final
zip ~/figures-final.zip ~/figures-final/*.pdf
echo "Done: ~/figures-final.zip"
```

---

## Lấy dữ liệu về local

```bash
# Trên máy local
scp tronghien1011@<IP_VM>:~/figures-N.zip E:\CODE\H_SAQMAODV\
scp tronghien1011@<IP_VM>:~/figures-S.zip E:\CODE\H_SAQMAODV\
scp tronghien1011@<IP_VM>:~/figures-E.zip E:\CODE\H_SAQMAODV\
scp tronghien1011@<IP_VM>:~/figures-L.zip E:\CODE\H_SAQMAODV\
scp tronghien1011@<IP_VM>:~/figures-TVI.zip E:\CODE\H_SAQMAODV\
scp tronghien1011@<IP_VM>:~/figures-final.zip E:\CODE\H_SAQMAODV\
```

---

## Push lên GitHub sau mỗi lần thay đổi

```bash
cd ~/hsaqmaodv-ns3
cp ~/run-paper1-experiments.sh hsaqmaodv/scripts/run/
cp ~/run-one-family.sh hsaqmaodv/scripts/run/
cp ~/run-all-families.sh hsaqmaodv/scripts/run/
cp ~/run-hqa-params.sh hsaqmaodv/scripts/run/
cp ~/plot-paper1.py hsaqmaodv/scripts/plot/
cp ~/ns-allinone-3.40-hsaqmaodv/ns-3.40/src/saqmaodv/model/saqmaodv-qtable.cc src/saqmaodv/model/
cp ~/ns-allinone-3.40-hsaqmaodv/ns-3.40/src/saqmaodv/model/saqmaodv-qtable.h src/saqmaodv/model/
cp ~/ns-allinone-3.40-hsaqmaodv/ns-3.40/src/saqmaodv/model/saqmaodv-routing-protocol.cc src/saqmaodv/model/
cp ~/ns-allinone-3.40-hsaqmaodv/ns-3.40/src/hsaqmaodv/model/hsaqmaodv-routing-protocol.cc src/hsaqmaodv/model/
git add .
git commit -m "chore: sync - <mô tả>"
git pull --rebase origin main && git push
```

---

## Bảng tóm tắt nhanh

| Kịch bản | Family | Seeds | Thời gian | Jobs | Output |
|---------|--------|-------|----------|------|--------|
| TVI sweep | TVI | 10 | ~20 phút | 6 | fig2_tvi_heatmap |
| Node density | N | 30 | ~2-3h | 3 | fig3_pdr_vs_n |
| Speed | S | 30 | ~2-3h | 3 | fig4_pdr_vs_speed |
| Energy | E | 30 | ~1h | 6 | fig5_pdr_vs_energy |
| Traffic load | L | 30 | ~1.5h | 4 | fig_pdr_vs_load |
| HQA params | — | 10 | ~2h | auto | custom analysis |
| Final (simTime=400) | N,S,E | 30 | ~8-10h | 3 | all figures |
