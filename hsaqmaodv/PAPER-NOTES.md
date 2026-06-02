# H-SAQMAODV — Paper / Report Notes

> Tài liệu này ghi lại toàn bộ motivation, design decisions, công thức toán học,
> phân tích reviewer, và contribution claims để phục vụ viết báo cáo / paper.
> Cập nhật theo tiến độ nghiên cứu.

---

## 1. Bối cảnh và Motivation

### 1.1 Các giao thức nền

| Giao thức | Đặc điểm chính | Hạn chế |
|---|---|---|
| **AODV** | Reactive, on-demand route discovery | Không multipath, không học |
| **PMAODV** | Multipath theo hop count | Không học từ kinh nghiệm |
| **QMAODV** | Q-learning multipath, reward = ACK + delay | ε, α cố định; không nhận thức năng lượng |
| **SAQMAODV** | Tự thích nghi ε, α, reward weights | Hard threshold năng lượng; variance cao khi mật độ thấp |
| **HSAQMAODV** | TVI 3-mode + smooth energy weights | **Đề xuất mới** |

### 1.2 Các nhận xét của reviewer về SAQMAODV (nguồn gốc của HSAQMAODV)

1. **Variance cao, hiệu suất chồng chéo ở 10–17 nút** — không giải thích được kỹ thuật.
2. **QMAODV là self-citation "to appear"** — khó xác minh độc lập.
3. **Tuyên bố "overhead không đáng kể" nhưng không có số liệu định lượng**.
4. **Hằng số hardcode** (+0.20 bump, 0.02 decay) không có sensitivity analysis.
5. **Hard threshold 20%** năng lượng gây bất ổn định routing đột ngột.

---

## 2. Đóng góp của H-SAQMAODV

### Contribution 1: Topology Volatility Indicator (TVI) + 3-mode switching

**Vấn đề giải quyết**: Reviewer comment #1 và #3.

**Định nghĩa (Eq. H.1)**:
```
TVI = ΔSeq_count / seqNoWindow_seconds
```
- `ΔSeq_count`: số lần cập nhật sequence number đích trong cửa sổ 5 giây
- `seqNoWindow_seconds = 5.0` (paper SAQMAODV §4.3)

**Ba chế độ hoạt động**:

```
TVI > tviHigh (default 3.0)  →  MODE_BYPASS
    Topology quá động → bỏ qua Q-table, dùng primary route (như AODV)
    Tác dụng: giảm overhead khám phá khi Q-table không đáng tin cậy
              → giải thích và fix variance cao ở mật độ thấp

tviLow ≤ TVI ≤ tviHigh       →  MODE_EXPLORE
    Trạng thái bình thường → epsilon-greedy của SAQMAODV
    Tác dụng: cân bằng khám phá / khai thác

TVI < tviLow  (default 1.0)  →  MODE_GREEDY
    Topology ổn định → khai thác Q-value cao nhất (ε = 0)
    Tác dụng: tối đa hoá hiệu suất khi Q đã hội tụ
```

**Lý giải kỹ thuật về variance cao ở mật độ thấp**:
- Mạng thưa (10–17 nút) → láng giềng ít → route thay đổi liên tục
- Mỗi topology change → `RecordSeqNoUpdate()` → ΔSeq tăng → TVI cao
- TVI cao → `MODE_BYPASS` → không gửi gói khám phá Q-table
- Kết quả: overhead giảm, variance giảm, hiệu suất ổn định hơn SAQMAODV
- **Đây là lời giải thích kỹ thuật cụ thể mà reviewer yêu cầu**

**Overhead measurement** (trả lời reviewer comment #3):
- `MODE_BYPASS`: 0 overhead bổ sung (chỉ dùng AODV primary route)
- `MODE_EXPLORE`: overhead tương đương SAQMAODV
- `MODE_GREEDY`: overhead thấp hơn EXPLORE (không có random exploration)
- CSV output: cột `routingOverhead` đo được định lượng theo protocol

---

### Contribution 2: Smooth Energy-Aware Reward Weighting (Sigmoid)

**Vấn đề giải quyết**: Reviewer comment #5 (hard threshold 20%).

**SAQMAODV (cũ — có vấn đề)**:
```
if E_res < 0.20: weights = (0.10, 0.10, 0.80)  ← flip đột ngột
else:            weights = (0.50, 0.40, 0.10)  ← flip về
```
Khi năng lượng dao động quanh 20%: weights flip liên tục → routing không ổn định.

**H-SAQMAODV (mới — sigmoid smooth)**:

Sigmoid activation (Eq. H.2):
```
s(E) = 1 / (1 + exp( (E − θ) / σ ))
```
- θ = 0.30 (soft threshold centre, thay vì hardcode 0.20)
- σ = 0.08 (transition width — điều chỉnh độ dốc chuyển tiếp)

Weight computation (Eq. H.3–H.5):
```
w3(E) = w3_hi + (w3_lo − w3_hi) · s(E)      [Eq. H.3]
w2(E) = w2_hi · (1 − s(E))                  [Eq. H.4]
w1(E) = 1 − w2(E) − w3(E)    [normalised]   [Eq. H.5]
```

Anchor values (từ SAQMAODV paper Table 1):
```
High-energy target: (w1, w2, w3) = (0.50, 0.40, 0.10)
Low-energy target:  (w1, w2, w3) = (0.10, 0.10, 0.80)
```

**Properties**:
| E | s(E) | w1 | w2 | w3 | Chế độ |
|---|---|---|---|---|---|
| 1.00 | ≈0.00 | ≈0.50 | ≈0.40 | ≈0.10 | Normal |
| 0.50 | 0.08 | ≈0.46 | ≈0.37 | ≈0.17 | Chuyển tiếp nhẹ |
| 0.30 (=θ) | 0.50 | ≈0.30 | ≈0.20 | ≈0.45 | Giữa chừng |
| 0.10 | 0.91 | ≈0.11 | ≈0.04 | ≈0.78 | Gần low-energy |
| 0.00 | ≈1.00 | ≈0.10 | ≈0.10 | ≈0.80 | Low-energy |

**Không có flip, không có hysteresis** → routing ổn định hơn.

---

## 3. Công thức toán học đầy đủ

### 3.1 Kế thừa từ SAQMAODV

**(1) Adaptive Exploration Rate (§4.2)**
```
On RERR:  ε_t = min(0.50, ε_t + 0.20)
Periodic: ε_t = max(0.10, ε_t − 0.02)
```

**(2) Adaptive Learning Rate (§4.3)**
```
α_t = 0.1 + 0.8 · (1 − exp(−λ · ΔSeq))     ∈ [0.1, 0.9]
```
- λ = 0.1 (sensitivity coefficient)
- ΔSeq = số SeqNo updates trong cửa sổ 5 giây

**(3) Q-update (Eq. 4)**
```
Q(dst, nh) ← (1 − α_t)·Q + α_t·[r_t + γ · max_Q(dst)]
```
- γ = 0.9 (discount factor, fixed)

### 3.2 Mới trong H-SAQMAODV

**(4) Topology Volatility Indicator (Eq. H.1)**
```
TVI = ΔSeq / 5.0
```

**(5) Mode selection**
```
mode = BYPASS   if TVI > tviHigh
mode = GREEDY   if TVI < tviLow
mode = EXPLORE  otherwise
```

**(6) Sigmoid activation (Eq. H.2)**
```
s(E) = 1 / (1 + exp( (E − 0.30) / 0.08 ))
```

**(7) Smooth weight update (Eq. H.3–H.5)**
```
w3 = 0.10 + (0.80 − 0.10) · s(E) = 0.10 + 0.70 · s(E)
w2 = 0.40 · (1 − s(E))
w1 = 1 − w2 − w3
```

**(8) 3-term reward (kế thừa từ SAQMAODV, với w_t từ Eq. H.3–H.5)**
```
r_t = w1·ACK_success + w2·(1/(delay+1)) + w3·E_residual
```

---

## 4. Hyperparameters

### 4.1 Kế thừa từ SAQMAODV (không đổi)

| Param | Giá trị | Nguồn |
|---|---|---|
| γ | 0.9 | SA-QMAODV paper fixed |
| ε₀ | 0.3 | SA-QMAODV paper |
| ε_min | 0.10 | SA-QMAODV paper |
| ε_max | 0.50 | SA-QMAODV paper |
| ε_bump | +0.20 | SA-QMAODV paper (cần sensitivity analysis) |
| ε_decay | −0.02 | SA-QMAODV paper (cần sensitivity analysis) |
| α₀ | 0.5 | Khởi tạo, sẽ adapt |
| λ | 0.1 | SA-QMAODV paper |
| seqNoWindow | 5.0s | SA-QMAODV paper §4.3 |
| adaptPeriod | 10.0s | Periodic tick |

### 4.2 Mới trong H-SAQMAODV

| Param | Giá trị mặc định | Ý nghĩa |
|---|---|---|
| tviHigh | 3.0 | TVI threshold cho BYPASS mode |
| tviLow | 1.0 | TVI threshold cho GREEDY mode |
| θ (theta) | 0.30 | Sigmoid centre (soft energy threshold) |
| σ (sigma) | 0.08 | Sigmoid steepness |

---

## 5. Sensitivity Analysis (cần thực hiện)

Reviewer yêu cầu sensitivity analysis cho các hằng số thực nghiệm.

### 5.1 Sensitivity cho TVI thresholds

Cần sweep:
- `tviHigh` ∈ {1.5, 2.0, 3.0, 4.0, 5.0}
- `tviLow`  ∈ {0.5, 1.0, 1.5, 2.0}

Metric quan sát: deliveryRatio, avgDelayMs, routingOverhead ở N=10,15,20

### 5.2 Sensitivity cho sigmoid parameters

- θ ∈ {0.20, 0.25, 0.30, 0.35, 0.40}
- σ ∈ {0.04, 0.08, 0.12, 0.16}

Metric quan sát: deliveryRatio, nodesDead ở heterogeneous battery scenario

### 5.3 Sensitivity kế thừa từ SAQMAODV

- ε_bump ∈ {0.10, 0.15, 0.20, 0.25}
- ε_decay ∈ {0.01, 0.02, 0.03}
- λ ∈ {0.05, 0.10, 0.20, 0.50}

---

## 6. Kịch bản thực nghiệm

### 6.1 Family N — Density sweep (trả lời reviewer comment #1)

Mục đích: chứng minh HSAQMAODV giảm variance ở mật độ thấp.

```
N ∈ {5, 10, 15, 20, 25, 30}
Protocols: AODV, PMAODV, QMAODV, SAQMAODV, HSAQMAODV
Seeds: 15
```

**Hypothesis**: tại N=10–17, HSAQMAODV có variance thấp hơn SAQMAODV
vì TVI cao → MODE_BYPASS → không overhead khám phá thêm.

### 6.2 Heterogeneous Battery

Mục đích: chứng minh smooth energy weighting ổn định hơn hard threshold.

```
initialEnergy ∈ {10, 20, 30, 50} J
simTime = 300s (đủ để pin cạn)
```

**Hypothesis**: số lần route flip ít hơn SAQMAODV khi E_res dao động quanh ngưỡng.

### 6.3 Overhead quantification (trả lời reviewer comment #3)

```
Metric: routingOverhead (packets) và routingOverhead/txPackets (ratio)
Compare: BYPASS vs EXPLORE vs GREEDY mode distribution theo N
```

### 6.4 TVI Sensitivity (Family H cho HSAQMAODV)

```
tviHigh ∈ {1.5, 2.0, 3.0, 4.0, 5.0}
tviLow  ∈ {0.5, 1.0, 1.5, 2.0}
N = 15, seeds = 5
```

---

## 7. Claims cho Paper

### Claim 1 (TVI mode switching)
> "H-SAQMAODV introduces a Topology Volatility Indicator (TVI) that dynamically
> selects among three routing modes. In low-density FANETs (10–17 nodes),
> where topology changes frequently, TVI exceeds the BYPASS threshold, causing
> H-SAQMAODV to revert to primary-route forwarding. This suppresses unnecessary
> Q-table exploration, reducing routing overhead by X% and packet delivery
> variance by Y% compared to SA-QMAODV."
> [X, Y to be filled from experiments]

### Claim 2 (Smooth energy weighting)
> "H-SAQMAODV replaces SA-QMAODV's hard energy threshold with a sigmoid-smooth
> transition function, eliminating abrupt reward-weight flips. In heterogeneous
> battery scenarios, this reduces routing instability events by Z% while
> maintaining comparable energy efficiency."
> [Z to be filled from experiments]

### Claim 3 (Overhead)
> "In MODE_BYPASS operation, H-SAQMAODV generates zero additional routing
> control overhead beyond standard AODV path discovery, formally supporting
> the 'negligible overhead' property under high-volatility conditions."

---

## 8. So sánh H-SAQMAODV vs SAQMAODV

| Khía cạnh | SAQMAODV | H-SAQMAODV |
|---|---|---|
| Route selection | Luôn epsilon-greedy | 3 modes theo TVI |
| Overhead ở topology động | Cao (vẫn explore) | Thấp (BYPASS mode) |
| Variance ở mật độ thấp | Cao | Thấp (BYPASS mode) |
| Energy weight update | Hard flip tại 20% | Sigmoid smooth, θ=0.30 |
| Routing stability near threshold | Không ổn định | Ổn định (monotone) |
| Thêm hyperparameters | 0 | +4: tviHigh, tviLow, θ, σ |

---

## 9. File Reference

| File | Mô tả |
|---|---|
| `files/hsaqmaodv-qtable.h` | Header: API + full design documentation |
| `files/hsaqmaodv-qtable.cc` | Implementation: sigmoid, TVI, hybrid routing |
| `files/saqmaodv-qtable.h` | Base class SA-QMAODV Q-table |
| `files/saqmaodv-qtable.cc` | Base class implementation |
| `hsaqmaodv/scripts/patches/apply-hsaqmaodv-module.py` | NS-3 module installer |
| `hsaqmaodv/scripts/patches/apply-hsaqmaodv-fanet.py` | fanet-sim.cc patcher |
| `src/fanet-sim.cc` | Simulation driver (5 protocols) |
| `scripts/setup/setup-hsaqmaodv-standalone.sh` | Full standalone VM setup |

---

*Last updated: 2026-06-02*
*Author: Le Trong-Hien, IUH Vietnam*
