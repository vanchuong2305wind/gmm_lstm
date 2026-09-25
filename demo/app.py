"""Demo tương tác DGM2: dự báo chuỗi thời gian đa biến thưa bằng hỗn hợp Gaussian động.

Chạy:  streamlit run app.py
"""
import json, os
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import torch
from sklearn.decomposition import PCA

from data import load_ushcn, drop_observations, FEATURES, W_PAST, R_FUTURE
from dgm2 import DGM2
from baselines import NaiveLast, LSTMForecaster

HERE = os.path.dirname(os.path.abspath(__file__))
CKPT, RES = os.path.join(HERE, "checkpoints"), os.path.join(HERE, "results")
COLORS = {"Thực tế": "#222222", "DGM2-L": "#d62728", "LSTM": "#1f77b4", "GMM-HMM": "#2ca02c", "Naive": "#9467bd"}

st.set_page_config(page_title="Demo DGM2", layout="wide")


@st.cache_resource
def load_everything():
    data = load_ushcn(0.0)
    ck = torch.load(os.path.join(CKPT, "dgm2_gate.pt"), weights_only=False)
    dgm2 = DGM2(d=5, **ck["cfg"]); dgm2.load_state_dict(ck["state"]); dgm2.eval()
    models = {"DGM2-L": dgm2}
    if os.path.exists(os.path.join(CKPT, "lstm.pt")):
        lstm = LSTMForecaster(5); lstm.load_state_dict(torch.load(os.path.join(CKPT, "lstm.pt"))["state"]); lstm.eval()
        models["LSTM"] = lstm
    if os.path.exists(os.path.join(CKPT, "hmm.pt")):
        models["GMM-HMM"] = torch.load(os.path.join(CKPT, "hmm.pt"), weights_only=False)
    models["Naive"] = NaiveLast()
    return data, models, ck


data, models, ck = load_everything()
dgm2 = models["DGM2-L"]
test = data["test"]

# ------------------------------------------------------------------ sidebar
st.sidebar.title("Tuỳ chọn")
idx = st.sidebar.number_input("Chỉ số mẫu kiểm thử", 0, len(test["x"]) - 1, 7)
extra = st.sidebar.slider("Xoá thêm quan sát ở 80 ngày quá khứ (%)", 0, 90, 0, 10) / 100
seed = st.sidebar.number_input("Seed xoá ngẫu nhiên", 0, 999, 0)
feats = st.sidebar.multiselect("Biến hiển thị", FEATURES, FEATURES)
show = st.sidebar.multiselect("Mô hình so sánh", list(models), list(models))

x = test["x"][idx:idx + 1]; m_full = test["m"][idx:idx + 1]
m_in = m_full.clone()
m_in[:, :W_PAST] = drop_observations(m_full[:, :W_PAST], extra, seed=int(seed))
xp, mp = x[:, :W_PAST] * m_in[:, :W_PAST], m_in[:, :W_PAST]

with torch.no_grad():
    preds = {n: models[n].forecast(xp, mp, R_FUTURE) for n in show if n in models}
    _, det = dgm2.forecast(xp, mp, R_FUTURE, return_details=True)

st.title("DGM2 – Dự báo chuỗi thời gian đa biến thưa bằng hỗn hợp Gaussian động")
st.caption(f"Bộ dữ liệu USHCN (khí hậu, 5 biến, 100 ngày/mẫu) · dùng {W_PAST} ngày quá khứ để dự báo {R_FUTURE} ngày · "
           f"tỉ lệ thiếu của mẫu này ở đoạn quá khứ: {100 * (1 - mp.mean()):.1f}%")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Dự báo", "🧩 Cụm tiềm ẩn & cổng γ", "🌐 Không gian cụm", "📊 Kết quả thực nghiệm"])

# ------------------------------------------------------------------ tab 1
with tab1:
    y, my = x[0, W_PAST:], m_full[0, W_PAST:]
    rows = []
    for n, p in preds.items():
        e = (p[0] - y) * my
        rows.append({"Mô hình": n, "RMSE": float(torch.sqrt((e ** 2).sum() / my.sum().clamp(min=1))),
                     "MAE": float(e.abs().sum() / my.sum().clamp(min=1))})
    st.subheader("Sai số trên mẫu đang chọn (không gian chuẩn hoá)")
    st.dataframe(rows, hide_index=True)

    sel = [FEATURES.index(f) for f in feats]
    if sel:
        fig, axes = plt.subplots(len(sel), 1, figsize=(12, 2.3 * len(sel)), sharex=True, squeeze=False)
        t_all = np.arange(W_PAST + R_FUTURE)
        x_in = det["x_in"][0].numpy()
        for ax, i in zip(axes[:, 0], sel):
            obs = m_in[0, :, i].numpy() > 0
            dropped = (m_full[0, :W_PAST, i].numpy() > 0) & ~obs[:W_PAST]
            ax.axvspan(W_PAST - 0.5, W_PAST + R_FUTURE, color="#f3f3f3")
            ax.plot(np.arange(W_PAST), x_in[:, i], "--", color="#ff7f0e", lw=1, label="Tiền nội suy (Eq. 2-3)")
            ax.scatter(t_all[obs], x[0, obs, i], s=10, color=COLORS["Thực tế"], label="Quan sát")
            ax.scatter(np.arange(W_PAST)[dropped], x[0, :W_PAST][dropped, i], s=14, facecolors="none",
                       edgecolors="#999999", label="Đã bị xoá (ẩn khỏi mô hình)")
            for n, p in preds.items():
                ax.plot(np.arange(W_PAST, W_PAST + R_FUTURE), p[0, :, i], color=COLORS[n], lw=1.8, label=n)
            ax.set_ylabel(FEATURES[i])
        axes[0, 0].legend(ncol=4, fontsize=8, loc="upper left")
        axes[-1, 0].set_xlabel("Ngày")
        fig.tight_layout()
        st.pyplot(fig)

# ------------------------------------------------------------------ tab 2
with tab2:
    st.markdown(r"""
**Quá khứ (ngày 1-80):** xác suất hậu nghiệm $q_\phi(z_t \mid \mathbf{x}_{1:t}, z_{t-1})$ từ mạng suy diễn.
**Tương lai (ngày 81-100):** phân phối hỗn hợp động $\boldsymbol\psi_{t} = (1-\gamma_t)\,p(z_{t}\mid z_{1:t-1}) + \gamma_t\,p(\boldsymbol\mu)$ (Eq. 4),
dự báo $\tilde{\mathbf{x}}_t = \sum_c \psi_t[c]\,\boldsymbol\mu_c$.""")
    heat = torch.cat([det["q_past"][0], det["psi"][0]], 0).numpy().T
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 5.5), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    im = a1.imshow(heat, aspect="auto", cmap="magma", interpolation="nearest")
    a1.axvline(W_PAST - 0.5, color="cyan", lw=1.5)
    a1.set_ylabel("Cụm c"); a1.set_title("Xác suất thuộc cụm theo thời gian")
    fig.colorbar(im, ax=a1, pad=0.01)
    g = torch.cat([det["gamma_past"][0, :, 0], det["gamma_future"][0, :, 0]]).numpy()
    a2.plot(g, color="#d62728"); a2.axvline(W_PAST - 0.5, color="cyan", lw=1.5)
    a2.set_ylabel("γ(h̃_t)"); a2.set_xlabel("Ngày")
    fig.tight_layout(); st.pyplot(fig)

    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.bar(np.arange(dgm2.k), dgm2.basis_prob.numpy(), color="#8c564b")
        ax.set_title("Phân phối hỗn hợp cơ sở p(μ) (Eq. 11)"); ax.set_xlabel("Cụm")
        fig.tight_layout(); st.pyplot(fig)
    with c2:
        seq = np.concatenate([det["q_past"][0].argmax(-1).numpy(), det["psi"][0].argmax(-1).numpy()])
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.step(np.arange(len(seq)), seq, where="mid", color="#17becf")
        ax.axvline(W_PAST - 0.5, color="gray", ls="--")
        ax.set_title("Chuỗi trạng thái cụm có xác suất lớn nhất"); ax.set_xlabel("Ngày"); ax.set_ylabel("Cụm")
        fig.tight_layout(); st.pyplot(fig)

# ------------------------------------------------------------------ tab 3
with tab3:
    st.markdown("Chiếu PCA 2 chiều của các vector đặc trưng $\\mathbf{x}_t$ (đã tiền nội suy) của 40 mẫu kiểm thử, "
                "tô màu theo cụm được gán; dấu **+** là các tâm Gaussian $\\boldsymbol\\mu_c$ học được "
                "(tương tự Hình 4 của bài báo).")
    xs, ms = test["x"][:40, :W_PAST], test["m"][:40, :W_PAST]
    with torch.no_grad():
        out = dgm2.filter(xs, ms, sample=False)
    feats_all = out["x_in"].reshape(-1, 5).numpy()
    lab = out["q"].reshape(-1, dgm2.k).argmax(-1).numpy()
    pca = PCA(2).fit(np.vstack([feats_all, dgm2.mu.detach().numpy()]))
    P, C = pca.transform(feats_all), pca.transform(dgm2.mu.detach().numpy())
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(P[:, 0], P[:, 1], c=lab, cmap="tab20", s=6, alpha=0.5)
    ax.scatter(C[:, 0], C[:, 1], marker="+", s=160, color="black", linewidths=2, label="μ_c")
    ax.legend(); ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
    fig.tight_layout(); st.pyplot(fig)

# ------------------------------------------------------------------ tab 4
with tab4:
    for name, title in [("main", "So sánh trên tập kiểm thử (1000 mẫu)"), ("ablation", "Phân tích ablation của γ"),
                        ("robustness", "Độ bền khi xoá thêm quan sát (RMSE)")]:
        f = os.path.join(RES, name + ".json")
        if not os.path.exists(f):
            continue
        st.subheader(title)
        r = json.load(open(f, encoding="utf8"))
        if name == "robustness":
            ratios = list(r)
            st.dataframe([{"Mô hình": mdl, **{f"{float(k)*100:.0f}%": round(r[k][mdl]["RMSE"], 4) for k in ratios}}
                          for mdl in r[ratios[0]]], hide_index=True)
        else:
            st.dataframe([{"Mô hình": k, "RMSE": round(v["RMSE"], 4), "MAE": round(v["MAE"], 4)} for k, v in r.items()],
                         hide_index=True)
    for img in ["robustness.png", "training_curve.png"]:
        p = os.path.join(RES, img)
        if os.path.exists(p):
            st.image(p)
