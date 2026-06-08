#!/bin/bash
# run-all-families.sh
# Chạy từng family độc lập trong tmux riêng
# Usage: bash run-all-families.sh [SEEDS]
# Example: bash run-all-families.sh 30

SEEDS=${1:-30}

echo "Khởi động tất cả families với SEEDS=$SEEDS"
echo "Mỗi family chạy trong tmux session riêng"
echo ""

# TVI — nhẹ nhất
tmux new-session -d -s fam-tvi \
  "bash ~/run-one-family.sh TVI 10; echo 'TVI DONE'; read"
echo "[OK] tmux fam-tvi started (TVI, seeds=10)"

sleep 2

# E — nhẹ
tmux new-session -d -s fam-e \
  "bash ~/run-one-family.sh E $SEEDS; echo 'E DONE'; read"
echo "[OK] tmux fam-e started (E, seeds=$SEEDS)"

sleep 2

# L — trung bình
tmux new-session -d -s fam-l \
  "bash ~/run-one-family.sh L $SEEDS; echo 'L DONE'; read"
echo "[OK] tmux fam-l started (L, seeds=$SEEDS)"

sleep 5

# N — nặng hơn
tmux new-session -d -s fam-n \
  "bash ~/run-one-family.sh N $SEEDS; echo 'N DONE'; read"
echo "[OK] tmux fam-n started (N, seeds=$SEEDS)"

sleep 5

# S — nặng nhất, chạy cuối
tmux new-session -d -s fam-s \
  "bash ~/run-one-family.sh S $SEEDS; echo 'S DONE'; read"
echo "[OK] tmux fam-s started (S, seeds=$SEEDS)"

echo ""
echo "Tất cả sessions đã khởi động. Kiểm tra:"
echo "  tmux ls"
echo "  tmux attach -t fam-<name>"
