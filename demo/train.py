"""Huấn luyện DGM2-L trên USHCN (80 ngày quá khứ -> dự báo 20 ngày).

    python train.py --epochs 40        # ~10 phút trên CPU, lưu checkpoints/dgm2.pt
"""
import argparse, json, os, time
import numpy as np
import torch

from data import load_ushcn, W_PAST, R_FUTURE
from dgm2 import DGM2

HERE = os.path.dirname(os.path.abspath(__file__))
CKPT = os.path.join(HERE, "checkpoints"); os.makedirs(CKPT, exist_ok=True)
RES = os.path.join(HERE, "results"); os.makedirs(RES, exist_ok=True)

# cấu hình chọn bằng grid search trên tập validation (logs/sweep*.log)
DGM2_CFG = dict(k=50, hidden=40, var=0.1, max_kl=1.0, lr=5e-3)


def metrics(pred, split, m_eval=None):
    """RMSE / MAE trên các giá trị quan sát được của 20 bước tương lai (không gian chuẩn hoá)."""
    y = split["x"][:, W_PAST:]
    m = split["m"][:, W_PAST:] if m_eval is None else m_eval
    err = (pred - y) * m
    n = m.sum()
    return {"RMSE": float(torch.sqrt((err ** 2).sum() / n)), "MAE": float(err.abs().sum() / n)}


def past(split):
    return split["x"][:, :W_PAST] * split["m_in"][:, :W_PAST], split["m_in"][:, :W_PAST]


def batched_forecast(model, split, bs=500):
    x, m = past(split)
    with torch.no_grad():
        return torch.cat([model.forecast(x[i:i + bs], m[i:i + bs], R_FUTURE) for i in range(0, len(x), bs)])


def load_dgm2(tag="dgm2"):
    ck = torch.load(os.path.join(CKPT, tag + ".pt"), weights_only=False)
    model = DGM2(d=5, **ck["cfg"]); model.load_state_dict(ck["state"]); model.eval()
    return model, ck


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


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=40)
    a = ap.parse_args()
    torch.set_num_threads(max(1, os.cpu_count() // 2))
    data = load_ushcn(0.0)
    model, _ = train_dgm2(data, epochs=a.epochs)
    res = metrics(batched_forecast(model, data["test"]), data["test"])
    print("test:", res)
    json.dump({**DGM2_CFG, "epochs": a.epochs}, open(os.path.join(RES, "config.json"), "w"), indent=2)
