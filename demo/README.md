# Demo DGM² – dự báo chuỗi thời gian đa biến thưa bằng hỗn hợp Gaussian động

Cài đặt lại gọn mô hình **DGM²-L** (Wu et al., AAAI 2021) bằng PyTorch, áp dụng dự báo khí hậu trên dữ liệu thưa
USHCN (80 ngày quá khứ → 20 ngày tương lai), kèm ứng dụng web tương tác. Chạy được hoàn toàn trên CPU.

## Cài đặt

```bash
pip install torch numpy matplotlib scikit-learn streamlit
```

## Chạy demo (dùng mô hình đã huấn luyện sẵn, nhẹ)

```bash
cd demo
streamlit run app.py          # mở http://localhost:8501
```

## Các lệnh khác

```bash
python evaluate.py            # đánh giá trên tập test -> results/eval.json (vài giây)
python make_figures.py        # vẽ hình vào results/ (khoảng 15 giây)
python train.py --epochs 40   # huấn luyện lại từ đầu (CPU, ~10-15 phút)
```

## Cấu trúc

| Tệp | Nội dung |
|---|---|
| `data.py` | Nạp USHCN (từ repo gốc), loại ngoại lai ±3σ, chuẩn hoá z-score, xoá thêm quan sát |
| `dgm2.py` | `PreImputation` (Eq. 2-3), `DGM2`: mạng sinh LSTM, hỗn hợp Gaussian động (Eq. 4), mạng suy diễn (Eq. 10), cổng γ, ELBO (Eq. 9), dự báo |
| `train.py` | Huấn luyện DGM²-L |
| `evaluate.py` | Sai số tổng / theo biến / theo tầm dự báo, độ bền khi dữ liệu thưa hơn, chất lượng nội suy |
| `make_figures.py` | Vẽ hình kết quả |
| `app.py` | Ứng dụng Streamlit |
| `data/` | Tensor USHCN (4000 train, 1000 test, 100 ngày × 5 biến) |
| `checkpoints/dgm2.pt` | Mô hình đã huấn luyện |
| `results/` | Kết quả JSON và hình |
| `logs/` | Log dò siêu tham số (`sweep*.log`) |

Nguồn dữ liệu và mã gốc: https://github.com/KnowledgeDiscovery/DynamicGaussianMixture
