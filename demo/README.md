# Demo DGM² – dự báo chuỗi thời gian đa biến thưa bằng hỗn hợp Gaussian động

Cài đặt lại gọn mô hình **DGM²-L** (Wu et al., AAAI 2021) bằng PyTorch, thí nghiệm trên dữ liệu khí hậu USHCN
(80 ngày quá khứ → dự báo 20 ngày), so sánh với GMM-HMM, LSTM và Naive, kèm ứng dụng web tương tác.

## Cài đặt

```bash
pip install torch numpy matplotlib scikit-learn hmmlearn streamlit
```

## Chạy nhanh (dùng checkpoint có sẵn)

```bash
cd demo
streamlit run app.py          # mở http://localhost:8501
```

## Huấn luyện lại toàn bộ

```bash
./run_all.sh                  # main + ablation + robustness + vẽ hình (CPU, ~40-60 phút)
# hoặc từng phần:
python train.py --exp main --epochs 40
python train.py --exp ablation --epochs 40
python train.py --exp robustness --epochs 30 --ratios 0.0 0.2 0.4 0.6 0.8
python make_figures.py
```

## Cấu trúc

| Tệp | Nội dung |
|---|---|
| `data.py` | Nạp USHCN (từ repo gốc), loại ngoại lai ±3σ, chuẩn hoá z-score, xoá thêm quan sát |
| `dgm2.py` | `PreImputation` (Eq. 2-3), `DGM2`: mạng sinh LSTM, hỗn hợp Gaussian động (Eq. 4), mạng suy diễn (Eq. 10), cổng γ, ELBO (Eq. 9), dự báo |
| `baselines.py` | Naive, GMM-HMM (hmmlearn), LSTM encoder–decoder |
| `train.py` | Huấn luyện / đánh giá, các thí nghiệm |
| `make_figures.py` | Vẽ hình kết quả vào `results/` |
| `app.py` | Ứng dụng Streamlit |
| `data/` | Tensor USHCN (4000 train, 1000 test, 100 ngày × 5 biến) |
| `checkpoints/` | Mô hình đã huấn luyện |
| `results/` | Kết quả JSON và hình |
| `logs/` | Log huấn luyện, grid search (`sweep*.log`) |

Nguồn dữ liệu và mã gốc: https://github.com/KnowledgeDiscovery/DynamicGaussianMixture
