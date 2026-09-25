"""Sinh các hình kết quả demo (lưu vào results/) để đưa vào báo cáo."""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
from sklearn.manifold import TSNE

from data import load_ushcn, FEATURES, W_PAST, R_FUTURE
from dgm2 import DGM2
from baselines import NaiveLast, LSTMForecaster

HERE = os.path.dirname(os.path.abspath(__file__))
CKPT, RES = os.path.join(HERE, "checkpoints"), os.path.join(HERE, "results")
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
COL = {"DGM2-L (gate)": "#d62728", "LSTM": "#1f77b4", "GMM-HMM": "#2ca02c", "Naive (last value)": "#9467bd"}


def load_models():
    ck = torch.load(os.path.join(CKPT, "dgm2_gate.pt"), weights_only=False)
    dgm2 = DGM2(d=5, **ck["cfg"]); dgm2.load_state_dict(ck["state"]); dgm2.eval()
    lstm = LSTMForecaster(5); lstm.load_state_dict(torch.load(os.path.join(CKPT, "lstm.pt"))["state"]); lstm.eval()
    hmm = torch.load(os.path.join(CKPT, "hmm.pt"), weights_only=False)
    return {"DGM2-L (gate)": dgm2, "GMM-HMM": hmm, "LSTM": lstm, "Naive (last value)": NaiveLast()}, ck


def fig_training_curve(ck):
    h = ck["hist"]; ep = [r["epoch"] for r in h]
    fig, ax = plt.subplots(1, 3, figsize=(12, 3))
    ax[0].plot(ep, [r["rec"] for r in h]); ax[0].set_title("−log-likelihood tái tạo / quan sát")
    ax[1].plot(ep, [r["kl"] for r in h], color="#ff7f0e"); ax[1].set_title("KL / bước thời gian")
    ax[2].plot(ep, [r["val_RMSE"] for r in h], color="#d62728"); ax[2].set_title("RMSE dự báo (validation)")
    for a in ax: a.set_xlabel("epoch")
    fig.tight_layout(); fig.savefig(os.path.join(RES, "training_curve.png"), dpi=200); plt.close(fig)


def fig_forecast(models, data, idx):
    test = data["test"]
    x, m = test["x"][idx:idx + 1], test["m"][idx:idx + 1]
    xp, mp = x[:, :W_PAST] * m[:, :W_PAST], m[:, :W_PAST]
    with torch.no_grad():
        preds = {n: mdl.forecast(xp, mp, R_FUTURE) for n, mdl in models.items()}
        _, det = models["DGM2-L (gate)"].forecast(xp, mp, R_FUTURE, return_details=True)
    fig, axes = plt.subplots(5, 1, figsize=(11, 9.5), sharex=True)
    t = np.arange(W_PAST + R_FUTURE)
    for i, ax in enumerate(axes):
        obs = m[0, :, i].numpy() > 0
        ax.axvspan(W_PAST - 0.5, W_PAST + R_FUTURE - 0.5, color="#f2f2f2")
        ax.plot(np.arange(W_PAST), det["x_in"][0, :, i], "--", color="#ff7f0e", lw=1, label="Tiền nội suy")
        ax.scatter(t[obs], x[0, obs, i], s=8, color="k", label="Quan sát thực tế", zorder=3)
        for n, p in preds.items():
            ax.plot(np.arange(W_PAST, W_PAST + R_FUTURE), p[0, :, i], color=COL[n], lw=1.7, label=n)
        ax.set_ylabel(FEATURES[i])
    axes[0].legend(ncol=3, fontsize=8, loc="upper left", frameon=False)
    axes[-1].set_xlabel("Ngày (vùng xám: 20 ngày cần dự báo)")
    fig.tight_layout(); fig.savefig(os.path.join(RES, f"forecast_example_{idx}.png"), dpi=200); plt.close(fig)

    heat = torch.cat([det["q_past"][0], det["psi"][0]], 0).numpy().T
    g = torch.cat([det["gamma_past"][0, :, 0], det["gamma_future"][0, :, 0]]).numpy()
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 4.8), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    im = a1.imshow(heat, aspect="auto", cmap="magma", interpolation="nearest")
    a1.axvline(W_PAST - 0.5, color="cyan", lw=1.5)
    a1.set_ylabel("Cụm c")
    a1.set_title("Trái vạch: hậu nghiệm q(z_t | x_1:t, z_t−1)   |   Phải vạch: hỗn hợp động ψ_t dùng để dự báo")
    a2.plot(g, color="#d62728"); a2.axvline(W_PAST - 0.5, color="cyan", lw=1.5)
    a2.set_ylabel("cổng γ_t"); a2.set_xlabel("Ngày")
    fig.tight_layout()
    fig.colorbar(im, ax=[a1, a2], pad=0.01, fraction=0.03); fig.savefig(os.path.join(RES, f"clusters_example_{idx}.png"), dpi=200); plt.close(fig)


def fig_tsne(model, data):
    """Tương tự Hình 4 của bài báo: t-SNE các đặc trưng x_t và các tâm mu."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, split, title in [(axes[0], "train", "(a) USHCN – tập huấn luyện"), (axes[1], "test", "(b) USHCN – tập kiểm thử")]:
        s = data[split]; n = 20
        with torch.no_grad():
            out = model.filter(s["x"][:n, :W_PAST], s["m"][:n, :W_PAST], sample=False)
        X = out["x_in"].reshape(-1, 5).numpy()
        mu = model.mu.detach().numpy()
        E = TSNE(2, init="pca", perplexity=30, random_state=0).fit_transform(np.vstack([X, mu]))
        P, C = E[:len(X)], E[len(X):]
        alpha = np.repeat(np.linspace(0.15, 1, n), W_PAST)
        ax.scatter(P[:, 0], P[:, 1], s=5, color="blue", alpha=alpha)
        used = model.basis_prob.numpy() > 1e-3
        ax.scatter(C[used, 0], C[used, 1], marker="+", s=90, color="#ff7f0e", linewidths=2)
        ax.set_title(title); ax.set_xticks([]); ax.set_yticks([])
    fig.tight_layout(); fig.savefig(os.path.join(RES, "tsne_clusters.png"), dpi=200); plt.close(fig)


def fig_robustness():
    f = os.path.join(RES, "robustness.json")
    if not os.path.exists(f):
        return
    r = json.load(open(f)); ratios = [float(k) for k in r]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    for ax, met in zip(axes, ["RMSE", "MAE"]):
        for mdl in r[list(r)[0]]:
            ax.plot(ratios, [r[k][mdl][met] for k in r], "o-", color=COL.get(mdl), label=mdl)
        ax.set_xlabel("Tỉ lệ quan sát bị xoá thêm δ"); ax.set_ylabel(met)
    axes[0].legend(fontsize=8, frameon=False)
    fig.tight_layout(); fig.savefig(os.path.join(RES, "robustness.png"), dpi=200); plt.close(fig)


if __name__ == "__main__":
    data = load_ushcn(0.0)
    models, ck = load_models()
    fig_training_curve(ck)
    import sys
    for idx in [7, 123]:
        fig_forecast(models, data, idx)
    if "--fast" not in sys.argv:
        fig_tsne(models["DGM2-L (gate)"], data)
    fig_robustness()
    print("done")
