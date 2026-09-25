#!/bin/bash
# Chạy toàn bộ thí nghiệm của demo (CPU). main trước, sau đó ablation & robustness song song.
cd "$(dirname "$0")"
python train.py --exp main --epochs 40 > logs/main.log 2>&1
python train.py --exp ablation --epochs 40 > logs/ablation.log 2>&1 &
python train.py --exp robustness --epochs 30 --ratios 0.0 0.2 0.4 > logs/rob_a.log 2>&1 &
python train.py --exp robustness --epochs 30 --ratios 0.6 0.8 > logs/rob_b.log 2>&1 &
wait
python -c "from train import merge_robustness; merge_robustness()"
python make_figures.py > logs/figures.log 2>&1
echo ALL_DONE
