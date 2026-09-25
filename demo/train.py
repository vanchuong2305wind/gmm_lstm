"""Huấn luyện & đánh giá DGM2-L và các baseline trên USHCN.

Ví dụ:
    python train.py --exp main          # so sánh chính (tỉ lệ thiếu gốc)
    python train.py --exp ablation      # gamma = 1 / 0 / 0.01 / cổng
    python train.py --exp robustness    # xoá thêm 0..80% quan sát
    python train.py --exp all
"""
import argparse, json, os, time
import numpy as np
import torch

from data import load_ushcn, W_PAST, R_FUTURE
from dgm2 import DGM2
from baselines import NaiveLast, GMMHMM, LSTMForecaster

HERE = os.path.dirname(os.path.abspath(__file__))
CKPT = os.path.join(HERE, "checkpoints"); os.makedirs(CKPT, exist_ok=True)
RES = os.path.join(HERE, "results"); os.makedirs(RES, exist_ok=True)


def metrics(pred, split):
    """RMSE / MAE trên các giá trị quan sát được của 20 bước tương lai (không gian chuẩn hoá)."""
    y, m = split["x"][:, W_PAST:], split["m"][:, W_PAST:]
    err = (pred - y) * m
    n = m.sum()
    return {"RMSE": float(torch.sqrt((err ** 2).sum() / n)), "MAE": float(err.abs().sum() / n)}


def past(split):
    return split["x"][:, :W_PAST] * split["m_in"][:, :W_PAST], split["m_in"][:, :W_PAST]


def batched_forecast(model, split, bs=500):
    x, m = past(split)
    return torch.cat([model.forecast(x[i:i + bs], m[i:i + bs], R_FUTURE) for i in range(0, len(x), bs)])


# ---------------------------------------------------------------- DGM2
# cấu hình mặc định chọn bằng grid search trên tập validation (logs/sweep*.log)
DGM2_CFG = dict(k=50, hidden=40, var=0.1, max_kl=1.0, lr=5e-3)


def train_dgm2(data, k=DGM2_CFG["k"], hidden=DGM2_CFG["hidden"], var=DGM2_CFG["var"], gamma=None, epochs=40,
               bs=128, lr=DGM2_CFG["lr"], max_kl=DGM2_CFG["max_kl"], soft_transition=True, seed=0, tag="dgm2",
               verbose=True):
    torch.manual_seed(seed); np.random.seed(seed)
    tr = data["train"]
    model = DGM2(d=tr["x"].shape[-1], k=k, hidden=hidden, var=var, gamma=gamma, soft_transition=soft_transition)
    model.init_mu_from_data(tr["x"], tr["m_in"])
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs)
    x_all, m_all = tr["x"] * tr["m_in"], tr["m_in"]     # huấn luyện trên toàn bộ 100 bước
    best, best_state, hist = 1e9, None, []
    for ep in range(epochs):
        model.train(); t0 = time.time()
        kl_w = min(1.0, (ep + 1) / (0.25 * epochs)) * max_kl   # KL annealing
        perm = torch.randperm(len(x_all)); logs = []
        for i in range(0, len(perm), bs):
            idx = perm[i:i + bs]
            loss, info = model.elbo(x_all[idx], m_all[idx], kl_weight=kl_w)
            opt.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0); opt.step()
            logs.append([loss.item(), info["rec"], info["kl"], info["gamma"]])
        sched.step()
        model.eval()
        val = metrics(batched_forecast(model, data["valid"]), data["valid"])
        l = np.mean(logs, 0)
        hist.append({"epoch": ep + 1, "loss": l[0], "rec": l[1], "kl": l[2], "gamma": l[3], **{"val_" + a: b for a, b in val.items()}})
        if val["RMSE"] < best:
            best, best_state = val["RMSE"], {a: b.clone() for a, b in model.state_dict().items()}
        if verbose:
            print(f"[{tag}] ep {ep+1:2d} loss {l[0]:.3f} rec {l[1]:.3f} kl {l[2]:.3f} gamma {l[3]:.3f} "
                  f"val RMSE {val['RMSE']:.4f} ({time.time()-t0:.1f}s)", flush=True)
    model.load_state_dict(best_state)
    cfg = dict(k=k, hidden=hidden, var=var, gamma=gamma, soft_transition=soft_transition)
    torch.save({"state": best_state, "cfg": cfg, "hist": hist}, os.path.join(CKPT, tag + ".pt"))
    return model, hist


# ---------------------------------------------------------------- LSTM
def train_lstm(data, epochs=40, bs=128, lr=3e-3, seed=0, tag="lstm", verbose=True):
    torch.manual_seed(seed)
    tr = data["train"]
    model = LSTMForecaster(tr["x"].shape[-1])
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    x, m = past(tr); y, my = tr["x"][:, W_PAST:], tr["m"][:, W_PAST:]
    best, best_state = 1e9, None
    for ep in range(epochs):
        model.train(); perm = torch.randperm(len(x))
        for i in range(0, len(perm), bs):
            idx = perm[i:i + bs]
            pred = model.forecast(x[idx], m[idx], R_FUTURE)
            loss = (((pred - y[idx]) * my[idx]) ** 2).sum() / my[idx].sum()
            opt.zero_grad(); loss.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            val = metrics(batched_forecast(model, data["valid"]), data["valid"])
        if val["RMSE"] < best:
            best, best_state = val["RMSE"], {a: b.clone() for a, b in model.state_dict().items()}
        if verbose and (ep + 1) % 5 == 0:
            print(f"[{tag}] ep {ep+1:2d} val RMSE {val['RMSE']:.4f}", flush=True)
    model.load_state_dict(best_state)
    torch.save({"state": best_state}, os.path.join(CKPT, tag + ".pt"))
    return model


def train_hmm(data, k=20, tag="hmm"):
    tr = data["train"]
    model = GMMHMM(k=k).fit(tr["x"] * tr["m_in"], tr["m_in"])
    torch.save(model, os.path.join(CKPT, tag + ".pt"))
    return model


def evaluate_all(data, models):
    with torch.no_grad():
        return {name: metrics(batched_forecast(mdl, data["test"]), data["test"]) for name, mdl in models.items()}


# ---------------------------------------------------------------- experiments
def exp_main(epochs):
    data = load_ushcn(0.0)
    models = {"Naive (last value)": NaiveLast(),
              "GMM-HMM": train_hmm(data),
              "LSTM": train_lstm(data, epochs=epochs),
              "DGM2-L (gate)": train_dgm2(data, epochs=epochs, tag="dgm2_gate")[0]}
    res = evaluate_all(data, models)
    print(json.dumps(res, indent=2))
    json.dump(res, open(os.path.join(RES, "main.json"), "w"), indent=2)
    json.dump({**DGM2_CFG, "epochs": epochs}, open(os.path.join(RES, "config.json"), "w"), indent=2)


def exp_ablation(epochs):
    data = load_ushcn(0.0)
    res = {}
    for name, g in [("gamma = 1.0 (GMM tĩnh)", 1.0), ("gamma = 0.0 (không có hỗn hợp cơ sở)", 0.0),
                    ("gamma = 0.01", 0.01), ("Cổng gamma(h)", None), ("Cổng gamma(h) + mẫu Gumbel-softmax", "gumbel")]:
        tag = "dgm2_gate" if g is None else f"dgm2_g{g}"
        if g == "gumbel":
            model = train_dgm2(data, epochs=epochs, soft_transition=False, tag="dgm2_gumbel")[0]
            res[name] = evaluate_all(data, {"m": model})["m"]; print(name, res[name], flush=True)
            continue
        if g is None and os.path.exists(os.path.join(CKPT, tag + ".pt")):
            ck = torch.load(os.path.join(CKPT, tag + ".pt"), weights_only=False)
            model = DGM2(d=5, **ck["cfg"]); model.load_state_dict(ck["state"]); model.eval()
        else:
            model = train_dgm2(data, gamma=g, epochs=epochs, tag=tag)[0]
        res[name] = evaluate_all(data, {"m": model})["m"]
        print(name, res[name], flush=True)
    json.dump(res, open(os.path.join(RES, "ablation.json"), "w"), indent=2)


def exp_robustness(epochs, ratios=(0.0, 0.2, 0.4, 0.6, 0.8)):
    for r in ratios:
        data = load_ushcn(r)
        models = {"Naive (last value)": NaiveLast(),
                  "GMM-HMM": train_hmm(data, tag=f"hmm_r{r}"),
                  "LSTM": train_lstm(data, epochs=epochs, tag=f"lstm_r{r}", verbose=False),
                  "DGM2-L (gate)": train_dgm2(data, epochs=epochs, tag=f"dgm2_r{r}", verbose=False)[0]}
        res = evaluate_all(data, models)
        print("missing drop", r, json.dumps(res), flush=True)
        json.dump(res, open(os.path.join(RES, f"robustness_{r}.json"), "w"), indent=2)
    merge_robustness()


def merge_robustness():
    """Gộp các file robustness_<r>.json (có thể chạy song song từng tỉ lệ) thành robustness.json."""
    import glob
    files = sorted(glob.glob(os.path.join(RES, "robustness_*.json")),
                   key=lambda f: float(os.path.basename(f)[11:-5]))
    res = {os.path.basename(f)[11:-5]: json.load(open(f)) for f in files}
    json.dump(res, open(os.path.join(RES, "robustness.json"), "w"), indent=2)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", default="main", choices=["main", "ablation", "robustness", "all"])
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--ratios", type=float, nargs="+", default=[0.0, 0.2, 0.4, 0.6, 0.8])
    a = ap.parse_args()
    torch.set_num_threads(max(1, os.cpu_count() // 2))
    if a.exp in ("main", "all"): exp_main(a.epochs)
    if a.exp in ("ablation", "all"): exp_ablation(a.epochs)
    if a.exp in ("robustness", "all"): exp_robustness(a.epochs, a.ratios)
