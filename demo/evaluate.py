"""Đánh giá DGM2-L đã huấn luyện (chỉ suy luận, không huấn luyện lại -> chạy nhẹ trên CPU).

    python evaluate.py       # ghi results/eval.json

Gồm:
  1. Sai số dự báo tổng trên tập test.
  2. Sai số theo từng biến và theo tầm dự báo (1..20 ngày).
  3. Độ bền: xoá ngẫu nhiên thêm delta = 0..80% quan sát ở 80 ngày quá khứ của tập test.
"""
import json, os
import torch

from data import load_ushcn, drop_observations, FEATURES, W_PAST, R_FUTURE
from train import load_dgm2, batched_forecast, metrics, RES


def rmse_mae(err, m):
    n = m.sum().clamp(min=1)
    return float(torch.sqrt(((err * m) ** 2).sum() / n)), float((err * m).abs().sum() / n)


def main():
    torch.manual_seed(0)
    data = load_ushcn(0.0)
    test = data["test"]
    model, _ = load_dgm2()
    out = {}

    # 1-2. tổng, theo biến, theo tầm dự báo
    pred = batched_forecast(model, test)
    y, m = test["x"][:, W_PAST:], test["m"][:, W_PAST:]
    out["overall"] = metrics(pred, test)
    out["per_variable"] = {FEATURES[i]: dict(zip(["RMSE", "MAE"], rmse_mae(pred[..., i] - y[..., i], m[..., i])))
                           for i in range(5)}
    out["per_horizon_rmse"] = [rmse_mae(pred[:, h] - y[:, h], m[:, h])[0] for h in range(R_FUTURE)]

    # 3. độ bền theo tỉ lệ xoá thêm (chỉ ở đầu vào của tập test)
    out["robustness"] = {}
    for r in [0.0, 0.2, 0.4, 0.6, 0.8]:
        split = dict(test)
        split["m_in"] = test["m"].clone()
        split["m_in"][:, :W_PAST] = drop_observations(test["m"][:, :W_PAST], r, seed=123)
        miss = 1 - split["m_in"][:, :W_PAST].mean().item()
        out["robustness"][str(r)] = {**metrics(batched_forecast(model, split), test), "missing_ratio": miss}

    json.dump(out, open(os.path.join(RES, "eval.json"), "w", encoding="utf8"), ensure_ascii=False, indent=2)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
