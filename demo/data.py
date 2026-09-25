"""Nạp và tiền xử lý bộ dữ liệu USHCN (lấy từ repo gốc của bài báo DGM2).

Mỗi mẫu là một chuỗi thời gian đa biến dài 100 ngày, 5 biến khí hậu của USHCN
(lượng mưa, tuyết rơi, độ dày tuyết, nhiệt độ cao nhất, nhiệt độ thấp nhất).
Nhiệm vụ: dùng 80 ngày quá khứ để dự báo 20 ngày tương lai.
"""
import os
import torch

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
# 5 đặc trưng khí hậu của USHCN (repo gốc không ghi rõ thứ tự cột nên đặt tên chung)
FEATURES = ["Biến 1", "Biến 2", "Biến 3", "Biến 4", "Biến 5"]
W_PAST, R_FUTURE = 80, 20


def _load(name):
    return torch.load(os.path.join(DATA_DIR, name), weights_only=False).float()


def _remove_outliers(x, m):
    m = m.clone()
    for i in range(x.shape[-1]):
        v = x[..., i][m[..., i] > 0]
        lo, hi = v.mean() - 3 * v.std(), v.mean() + 3 * v.std()
        m[..., i] *= ((x[..., i] >= lo) & (x[..., i] <= hi)).float()
    return m


def drop_observations(mask, ratio, seed=0):
    """Xoá ngẫu nhiên thêm `ratio` phần trăm giá trị đang quan sát được (thí nghiệm độ bền)."""
    if ratio <= 0:
        return mask.clone()
    g = torch.Generator().manual_seed(seed)
    keep = (torch.rand(mask.shape, generator=g) >= ratio).float()
    return mask * keep


def load_ushcn(missing_ratio=0.0, valid_frac=0.125, seed=0):
    """Trả về dict gồm train/valid/test đã chuẩn hoá z-score theo từng biến.

    x: (N, 100, 5)   giá trị (tại vị trí thiếu đặt = 0)
    m: (N, 100, 5)   mặt nạ quan sát (1 = quan sát được)
    missing_ratio chỉ áp dụng lên phần 80 bước quá khứ (đầu vào), phần tương lai
    giữ nguyên để đánh giá công bằng.
    """
    x_tr, m_tr = _load("training_samples"), _load("training_masks")
    x_te, m_te = _load("test_samples"), _load("test_masks")
    # vị trí thiếu trong dữ liệu gốc là NaN -> đưa về 0 và bảo đảm mask = 0 tại đó
    m_tr, m_te = m_tr * ~torch.isnan(x_tr), m_te * ~torch.isnan(x_te)
    x_tr, x_te = torch.nan_to_num(x_tr), torch.nan_to_num(x_te)

    # giống repo gốc: loại ngoại lai ngoài khoảng mean ± 3 std (đánh dấu thành "thiếu")
    m_tr, m_te = _remove_outliers(x_tr, m_tr), _remove_outliers(x_te, m_te)

    # chuẩn hoá theo thống kê của các giá trị quan sát được trong tập train
    obs = m_tr.bool()
    mean = torch.stack([x_tr[..., i][obs[..., i]].mean() for i in range(x_tr.shape[-1])])
    std = torch.stack([x_tr[..., i][obs[..., i]].std() for i in range(x_tr.shape[-1])])
    norm = lambda x, m: ((x - mean) / std) * m

    g = torch.Generator().manual_seed(seed)
    perm = torch.randperm(x_tr.shape[0], generator=g)
    n_val = int(valid_frac * x_tr.shape[0])
    idx_val, idx_tr = perm[:n_val], perm[n_val:]

    def split(x, m, sd):
        m_in = m.clone()
        m_in[:, :W_PAST] = drop_observations(m[:, :W_PAST], missing_ratio, seed=sd)
        return {"x": norm(x, m), "m": m, "m_in": m_in}

    return {
        "train": split(x_tr[idx_tr], m_tr[idx_tr], seed + 1),
        "valid": split(x_tr[idx_val], m_tr[idx_val], seed + 2),
        "test": split(x_te, m_te, seed + 3),
        "mean": mean, "std": std,
    }
