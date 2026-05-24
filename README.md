# H-SAQMAODV — Topology-Aware Hybrid Self-Adaptive Q-Learning Multipath AODV

[![NS-3](https://img.shields.io/badge/NS--3-3.40-blue)](https://www.nsnam.org/)
[![Status](https://img.shields.io/badge/status-in--development-yellow)]()
[![Based on](https://img.shields.io/badge/extends-SA--QMAODV-green)]()

## Tóm tắt

**H-SAQMAODV** (Hybrid Self-Adaptive Q-learning Multipath AODV) mở rộng SA-QMAODV bằng cơ chế
**Topology-Aware Q-Switching**: giao thức tự phát hiện trạng thái topology mạng và quyết định khi nào
dùng Q-learning, khi nào fallback về routing tất định — giải quyết điểm yếu cốt lõi của SA-QMAODV
khi mật độ UAV cao hoặc topology thay đổi quá nhanh.

### Cải tiến so với SA-QMAODV

| Thành phần | SA-QMAODV | H-SAQMAODV |
|---|---|---|
| Route selection | ε-greedy luôn active | **3-mode switching** theo ΔSeq |
| High-dynamic response | Exploration làm tăng loss | **Bypass Q → dùng primary route** |
| Stable network | Vẫn explore không cần thiết | **Pure greedy (ε→0)** |
| Medium dynamic | ε-greedy bình thường | ε-greedy bình thường |

### 3-Mode Topology-Aware Switching (đóng góp mới)

```
ΔSeq > ThreshHigh  →  MODE_BYPASS:  dùng primary route trực tiếp (AODV-like)
ΔSeq < ThreshLow   →  MODE_GREEDY:  chọn route có Q-value cao nhất (ε=0)
ThreshLow ≤ ΔSeq ≤ ThreshHigh → MODE_EXPLORE: ε-greedy bình thường
```

### Cảm hứng từ

- **HQA** (Hybrid Q-learning and AODV, ScienceDirect 2025): Bayesian stability evaluator
  → H-SAQMAODV dùng ΔSeq (đã có sẵn trong SA framework) thay vì Bayesian riêng biệt

---

## Cấu trúc project

```
paper1-hsaqmaodv/
├── README.md                        # File này
├── PAPER-OUTLINE.md                 # Cấu trúc bài báo
├── files/
│   ├── hsaqmaodv-qtable.h           # Extended QTable với 3-mode switching
│   └── hsaqmaodv-qtable.cc          # Implementation
├── scripts/
│   ├── patches/
│   │   └── apply-hsaqmaodv-*.py     # Patches để wire vào NS-3
│   ├── run/
│   │   └── run-paper1-experiments.sh
│   └── plot/
│       └── plot-paper1.py
└── notes/
    └── implementation-guide.md      # Hướng dẫn implement từng bước
```

## Base project

Kế thừa từ: `../` (saqmaodv-ns3) — dùng lại toàn bộ setup, patches AODV/AOMDV/PMAODV/QMAODV.
Chỉ thêm module `hsaqmaodv` thay thế `saqmaodv`.

## Setup

```bash
# Sau khi đã setup saqmaodv-ns3 thành công:
cd paper1-hsaqmaodv
bash scripts/patches/apply-hsaqmaodv-all.sh
# Build lại NS-3
cd $NS3_DIR && ./ns3 build
```

## Experiments

```bash
bash scripts/run/run-paper1-experiments.sh
```

## Target venue

IEEE/ACM conference on wireless networks / FANET — 2026
