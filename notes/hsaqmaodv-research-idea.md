# H-SAQMAODV: Ý tưởng nghiên cứu và kế hoạch so sánh

## 1. Bối cảnh và động lực

Mạng FANET (Flying Ad Hoc Network) với các UAV di động cao đặt ra thách thức đặc thù cho giao thức định tuyến: topology thay đổi liên tục, năng lượng pin hạn chế, và không có cơ sở hạ tầng cố định. Các giao thức truyền thống như AODV phản ứng chậm với thay đổi topology; các giao thức học tăng cường (Q-learning) lại kém ổn định khi môi trường quá động vì exploration gây mất gói tin.

Nghiên cứu này giải quyết câu hỏi: **Làm thế nào để giao thức định tuyến tự nhận biết trạng thái topology và điều chỉnh chiến lược học phù hợp — không học khi môi trường quá động, học tích cực khi ổn định?**

---

## 2. Chuỗi tiến hóa giao thức

### 2.1 AODV (Baseline)
- Reactive routing, single path, không học
- Ưu điểm: đơn giản, ổn định
- Nhược điểm: không tối ưu, không thích nghi

### 2.2 PMAODV
- Mở rộng AODV sang multipath (chọn theo hop count)
- Tăng độ tin cậy nhờ path redundancy
- Chưa có cơ chế học

### 2.3 QMAODV
- Thêm Q-table, chọn route theo ε-greedy
- Reward = w₁·ACK + w₂·1/(delay+1)
- Đột phá: giao thức bắt đầu học từ kinh nghiệm

### 2.4 SA-QMAODV (Self-Adaptive QMAODV)
Ba cơ chế adaptive độc lập:

**Adaptive ε (Exploration rate):**
- Tăng ε khi nhận RERR: ε ← min(ε_max, ε + 0.20)
- Giảm dần định kỳ: ε ← max(ε_min, ε − 0.02)

**Adaptive α (Learning rate):**
$$\alpha_t = 0.1 + 0.8 \cdot (1 - e^{-\lambda \cdot \Delta Seq})$$
- ΔSeq = số lần cập nhật sequence number trong cửa sổ thời gian
- α cao khi topology thay đổi nhanh → học nhanh hơn

**Adaptive Reward Weights:**
- Chế độ bình thường: (w₁, w₂, w₃) = (0.5, 0.4, 0.1)
- Chế độ tiết kiệm năng lượng (pin < 20%): (w₁, w₂, w₃) = (0.1, 0.1, 0.8)

### 2.5 H-SAQMAODV (Đóng góp chính — v1)

**Topology Volatility Index (TVI):**
$$TVI = \frac{\Delta Seq_{count}}{window_{seconds}}$$

TVI đo tốc độ thay đổi topology dựa trên tần suất cập nhật sequence number trong cửa sổ thời gian trượt.

**3-Mode Topology-Aware Switching:**

| Điều kiện | Mode | Hành vi |
|-----------|------|---------|
| TVI > TVI_high | BYPASS | Dùng primary route (AODV-like) |
| TVI < TVI_low | GREEDY | Chọn Q-value cao nhất (ε=0) |
| TVI_low ≤ TVI ≤ TVI_high | EXPLORE | ε-greedy bình thường |

**Lý do:** Khi topology quá động (TVI cao), Q-learning không kịp converge và exploration gây mất gói. Khi topology ổn định (TVI thấp), không cần explore — khai thác knowledge tốt nhất. Switching thông minh cho phép giao thức thích nghi với từng trạng thái mạng.

---

## 3. Cải tiến H-SAQMAODV v2

### 3.1 Enhanced BYPASS
**Vấn đề v1:** BYPASS dùng 1 path duy nhất như AODV, bỏ qua hoàn toàn Q-learning.

**Cải tiến:** BYPASS dùng greedy (ε=0) thay vì single path — vẫn chọn path tốt nhất theo Q-value nhưng không explore. An toàn khi topology động, không lãng phí knowledge tích lũy.

### 3.2 Hysteresis cho mode switching
**Vấn đề v1:** Mode có thể flip liên tục khi TVI dao động quanh ngưỡng.

**Cải tiến:** Chỉ đổi mode khi điều kiện giữ nguyên N tick liên tiếp (mặc định N=3). Giảm oscillation, tăng ổn định.

### 3.3 Congestion-Aware Reward
**Vấn đề v1:** Reward không phản ánh tình trạng tắc nghẽn.

**Cải tiến:**
$$r_t = w_1 \cdot ACK + w_2 \cdot \frac{1}{delay+1} + w_3 \cdot E_{res} + w_4 \cdot (1 - queueOcc)$$

Khuyến khích chọn path ít tắc nghẽn, hiệu quả nhất khi mật độ node cao.

### 3.4 Proportional ε Bump
**Vấn đề v1:** Mỗi RERR tăng ε cố định +0.20, bất kể mức độ nghiêm trọng.

**Cải tiến:**
$$bump = \min(0.40, \epsilon_{bump} \cdot (1 + errRate))$$

errRate = tần suất RERR trong cửa sổ 10 giây. Phản ứng mạnh khi mạng đang bất ổn liên tục, nhẹ khi chỉ có lỗi đơn lẻ.

---

## 4. Chiến lược so sánh — Tái triển khai HQA

### 4.1 Tại sao HQA?

HQA (Hybrid Q-learning AODV, 2025) là paper gần nhất về concept với H-SAQMAODV:
- Cùng ý tưởng switching giữa Q-learning và AODV reactive
- HQA dùng **Bayesian stability evaluator** để quyết định switch
- H-SAQMAODV dùng **TVI (ΔSeq-based)** — đơn giản hơn, không cần Bayesian riêng biệt
- Reviewer CHẮC CHẮN hỏi về HQA khi thấy H-SAQMAODV

HQA công bố: cải thiện PDR 5.4–9.1%, giảm delay 13.6–23.9% so với AODV.

### 4.2 Kế hoạch tái triển khai HQA trên NS-3

**Core của HQA cần implement:**

1. **Bayesian Stability Evaluator:**
$$P(stable | obs) \propto P(obs | stable) \cdot P(stable)$$
Dựa trên: số RERR gần đây, ΔSeq, hello loss rate.

2. **Dual-update reward mechanism:**
$$Q(s,a) \leftarrow (1-\alpha)Q(s,a) + \alpha[r_{link} + \gamma \cdot \max Q(s',a')]$$
Trong đó r_link bao gồm cả link stability score.

3. **Switching rule:**
- P(stable) > threshold → Q-learning mode
- P(stable) ≤ threshold → AODV reactive mode

**Lý do khả thi trên NS-3:**
- Bayesian evaluator chỉ là công thức xác suất, không tốn compute
- Có thể xây dựng trên QTable hiện có của saqmaodv
- Hardware requirement tương đương SAQMAODV

**Cách viết trong paper:**
> *"We re-implemented HQA [ref] following the algorithmic description in the original paper, integrated into NS-3.40 under identical simulation conditions (Gauss-Markov mobility, same node density, same traffic parameters)."*

### 4.3 Điểm khác biệt cần làm nổi bật

| Tiêu chí | HQA | H-SAQMAODV |
|---------|-----|------------|
| Stability metric | Bayesian (probabilistic) | TVI (deterministic, lightweight) |
| Switching granularity | Binary (Q-learning / AODV) | 3-mode (BYPASS / EXPLORE / GREEDY) |
| Energy awareness | Không có | Sigmoid-based adaptive weights |
| Overhead | Bayesian update mỗi packet | ΔSeq counter — O(1) |
| Adaptivity | ε fixed sau switch | ε adaptive liên tục (SA framework) |

---

## 5. Kịch bản thí nghiệm đề xuất

Để so sánh fair với HQA và các baseline khác:

**Protocols:** AODV, QMAODV, SAQMAODV, HQA (re-implemented), H-SAQMAODV

**Metrics:** PDR, End-to-end delay, Throughput, Energy consumption, Routing overhead

**Families:**
- **N:** Node density (5, 10, 15, 20, 25, 30 nodes)
- **S:** Mobility speed (5, 10, 20, 30, 50 m/s)
- **E:** Battery capacity (10, 20, 30, 50 J)
- **L:** Traffic load (pktInterval = 0.05–1.0 s)
- **TVI:** TVI threshold sensitivity (tviHigh × tviLow heatmap)

**Setup:** NS-3.40, Gauss-Markov mobility, 802.11a PHY, simTime=200s, 10 seeds/scenario

---

## 6. Định hướng publication

**Target Q3 (khả thi với kết quả tốt):**
- IEEE Access (open access, Q2)
- Ad Hoc Networks — Elsevier (Q2/Q3)
- Wireless Networks — Springer (Q3)
- EURASIP Journal on Wireless Communications (Q3)

**Điều kiện để submit:**
1. H-SAQMAODV cải thiện ≥ 5% PDR so với SAQMAODV với statistical significance
2. So sánh được với HQA (re-implemented)
3. Ít nhất 2 scenario families cho thấy lợi thế rõ ràng
4. Energy advantage thể hiện trong family E với simTime dài (≥ 400s)

---

## 7. Rủi ro và phương án dự phòng

**Rủi ro 1:** Kết quả H-SAQMAODV không vượt trội rõ ràng so với SAQMAODV.
→ Phương án: nhấn mạnh **robustness** (variance thấp hơn) thay vì mean PDR; thêm scenario tốc độ cao (speed=50 m/s) nơi BYPASS có lợi thế rõ nhất.

**Rủi ro 2:** HQA re-implementation không đúng, reviewer phản bác.
→ Phương án: ghi rõ *"approximate re-implementation"*, so sánh xu hướng thay vì số tuyệt đối; hoặc bỏ HQA và thêm AOMDV + DSDV làm baseline đơn giản hơn.

**Rủi ro 3:** Novelty bị đánh giá thấp.
→ Phương án: nhấn mạnh **lightweight TVI** (O(1) overhead) vs Bayesian (O(n) per packet); thêm phân tích computational overhead.
