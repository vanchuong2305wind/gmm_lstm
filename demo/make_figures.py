"""Sinh các hình kết quả của DGM2-L (lưu vào results/) để đưa vào báo cáo. Chỉ suy luận, chạy nhẹ.

    python make_figures.py          # cần results/eval.json (chạy evaluate.py trước)
"""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import torch
from sklearn.manifold import TSNE

from data import load_ushcn, FEATURES, W_PAST, R_FUTURE
from train import load_dgm2, RES

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
RED = "#d62728"


def mixture_std(model, psi):
    """Độ lệch chuẩn của hỗn hợp Gaussian sum_c psi_c N(mu_c, var I) theo từng biến."""
    mean = psi @ model.mu
    second = psi @ (model.mu ** 2) + model.var
    return (second - mean ** 2).clamp(min=0).sqrt()


def fig_training_curve(ck):
    h = ck["hist"]; ep = [r["epoch"] for r in h]
    fig, ax = plt.subplots(1, 3, figsize=(12, 3))
    ax[0].plot(ep, [r["rec"] for r in h]); ax[0].set_title("−log-likelihood tái tạo / quan sát")
    ax[1].plot(ep, [r["kl"] for r in h], color="#ff7f0e"); ax[1].set_title("KL / bước thời gian")
    ax[2].plot(ep, [r["val_RMSE"] for r in h], color=RED); ax[2].set_title("RMSE dự báo (validation)")
    for a in ax: a.set_xlabel("epoch")
    fig.tight_layout(); fig.savefig(os.path.join(RES, "training_curve.png"), dpi=200); plt.close(fig)


def fig_forecast(model, data, idx):
    test = data["test"]
    x, m = test["x"][idx:idx + 1], test["m"][idx:idx + 1]
    xp, mp = x[:, :W_PAST] * m[:, :W_PAST], m[:, :W_PAST]
    with torch.no_grad():
        pred, det = model.forecast(xp, mp, R_FUTURE, return_details=True)
        sd = mixture_std(model, det["psi"])
    tf = np.arange(W_PAST, W_PAST + R_FUTURE)
    fig, axes = plt.subplots(5, 1, figsize=(11, 9.5), sharex=True)
    t = np.arange(W_PAST + R_FUTURE)
    for i, ax in enumerate(axes):
        obs = m[0, :, i].numpy() > 0
        ax.axvspan(W_PAST - 0.5, W_PAST + R_FUTURE - 0.5, color="#f2f2f2")
        ax.plot(np.arange(W_PAST), det["x_in"][0, :, i], "--", color="#ff7f0e", lw=1, label="Tiền nội suy (Eq. 2-3)")
        ax.scatter(t[obs], x[0, obs, i], s=8, color="k", label="Quan sát thực tế", zorder=3)
        ax.fill_between(tf, pred[0, :, i] - sd[0, :, i], pred[0, :, i] + sd[0, :, i], color=RED, alpha=0.15,
                        label="±1 độ lệch chuẩn của hỗn hợp ψ_t")
        ax.plot(tf, pred[0, :, i], color=RED, lw=1.8, label="Dự báo DGM²-L")
        ax.set_ylabel(FEATURES[i])
    axes[0].legend(ncol=4, fontsize=8, loc="upper left", frameon=False)
    axes[-1].set_xlabel("Ngày (vùng xám: 20 ngày cần dự báo)")
    fig.tight_layout(); fig.savefig(os.path.join(RES, f"forecast_example_{idx}.png"), dpi=200); plt.close(fig)

    heat = torch.cat([det["q_past"][0], det["psi"][0]], 0).numpy().T
    g = torch.cat([det["gamma_past"][0, :, 0], det["gamma_future"][0, :, 0]]).numpy()
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 4.8), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    im = a1.imshow(heat, aspect="auto", cmap="magma", interpolation="nearest")
    a1.axvline(W_PAST - 0.5, color="cyan", lw=1.5)
    a1.set_ylabel("Cụm c")
    a1.set_title("Trái vạch: hậu nghiệm q(z_t | x_1:t, z_t−1)   |   Phải vạch: hỗn hợp động ψ_t dùng để dự báo")
    a2.plot(g, color=RED); a2.axvline(W_PAST - 0.5, color="cyan", lw=1.5)
    a2.set_ylabel("cổng γ_t"); a2.set_xlabel("Ngày")
    fig.tight_layout()
    fig.colorbar(im, ax=[a1, a2], pad=0.01, fraction=0.03)
    fig.savefig(os.path.join(RES, f"clusters_example_{idx}.png"), dpi=200); plt.close(fig)


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


def fig_eval():
    ev = json.load(open(os.path.join(RES, "eval.json"), encoding="utf8"))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.6))
    a1.plot(np.arange(1, R_FUTURE + 1), ev["per_horizon_rmse"], "o-", color=RED, ms=4)
    a1.set_xlabel("Tầm dự báo (ngày)"); a1.set_ylabel("RMSE"); a1.set_title("(a) Sai số theo tầm dự báo")
    rb = ev["robustness"]
    miss = [100 * rb[k]["missing_ratio"] for k in rb]
    a2.plot(miss, [rb[k]["RMSE"] for k in rb], "o-", color=RED, label="RMSE")
    a2.plot(miss, [rb[k]["MAE"] for k in rb], "s--", color="#1f77b4", label="MAE")
    a2.set_ylim(0, max(rb[k]["RMSE"] for k in rb) * 1.25)
    a2.set_xlabel("Tỉ lệ thiếu thực tế của 80 ngày đầu vào (%)"); a2.set_title("(b) Độ bền khi dữ liệu thưa hơn")
    a2.legend(frameon=False)
    fig.tight_layout(); fig.savefig(os.path.join(RES, "eval_horizon_robustness.png"), dpi=200); plt.close(fig)


if __name__ == "__main__":
    data = load_ushcn(0.0)
    model, ck = load_dgm2()
    fig_training_curve(ck)
    fig_forecast(model, data, 123)
    fig_eval()
    if "--fast" not in sys.argv:
        fig_tsne(model, data)
    print("done")
