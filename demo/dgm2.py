"""Cài đặt gọn của DGM2-L (Wu et al., AAAI 2021) bằng PyTorch.

Các thành phần tương ứng với bài báo:
    PreImputation         -> Eq. (2), (3)   lớp tiền nội suy bằng kernel Gaussian
    DGM2.gen_cell/p_mlp   -> Eq. (5)        mạng sinh: chuyển trạng thái cụm z_t -> z_{t+1}
    DGM2.mu, basis_prob   -> Eq. (4), (11)  hỗn hợp Gaussian động (phân phối cơ sở + điều chỉnh)
    DGM2.enc/q_mlp        -> Eq. (8), (10)  mạng suy diễn có cấu trúc q(z_t | x_{1:t}, z_{t-1})
    DGM2.gate             -> gamma(h~_t)    hàm cổng thay cho siêu tham số gamma
    DGM2.elbo             -> Eq. (9)        cận dưới biến phân (ELBO)
    DGM2.forecast         -> dự báo r bước tiếp theo bằng kỳ vọng của hỗn hợp động
"""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class PreImputation(nn.Module):
    """Lớp tiền nội suy (Eq. 2-3).

    kappa(t*, t; alpha_i) = exp(-alpha_i (t* - t)^2)
    x_bar^i_{t*}  = sum_t kappa m^i_t x^i_t / lambda(t*, m^i; alpha_i)
    x_hat^i_{t*}  = sum_j rho_ij lambda_j x_bar^j_{t*} / sum_j |rho_ij| lambda_j
    (mẫu số dùng |rho_ij| để x_hat luôn là một trung bình có trọng số)
    """

    def __init__(self, d, time_scale=100.0, init_bandwidth=3.0):
        super().__init__()
        self.d, self.time_scale = d, time_scale
        # alpha_i = softplus(raw) > 0; khởi tạo sao cho độ rộng kernel ~ init_bandwidth bước
        a0 = 1.0 / (2 * (init_bandwidth / time_scale) ** 2)
        self.raw_alpha = nn.Parameter(torch.full((d,), math.log(math.expm1(a0))))
        self.rho_offdiag = nn.Parameter(torch.zeros(d, d))

    @property
    def alpha(self):
        return F.softplus(self.raw_alpha)

    @property
    def rho(self):
        eye = torch.eye(self.d, device=self.rho_offdiag.device)
        return eye + self.rho_offdiag * (1 - eye)       # rho_ii = 1

    def forward(self, x, m, T_ref=None):
        """x, m: (B, T, d). T_ref: số điểm thời gian tham chiếu cần nội suy (mặc định = T)."""
        B, T, d = x.shape
        T_ref = T_ref or T
        t = torch.arange(T, device=x.device, dtype=x.dtype) / self.time_scale
        ts = torch.arange(T_ref, device=x.device, dtype=x.dtype) / self.time_scale
        diff2 = (ts[:, None] - t[None, :]) ** 2                               # (T_ref, T)
        K = torch.exp(-self.alpha[:, None, None] * diff2[None])                # (d, T_ref, T)
        lam = torch.einsum("isu,bui->bsi", K, m)                               # cường độ lambda
        num = torch.einsum("isu,bui->bsi", K, m * x)
        x_bar = num / (lam + 1e-6)                                             # Eq. (2)
        w = self.rho[None, None] * lam[:, :, None, :]                          # (B,T_ref,i,j)
        x_hat = (w * x_bar[:, :, None, :]).sum(-1) / (w.abs().sum(-1) + 1e-6)  # Eq. (3)
        return x_hat, lam


class DGM2(nn.Module):
    def __init__(self, d, k=30, hidden=40, var=0.1, gamma=None, tau=0.5, soft_transition=True):
        """
        d: số biến; k: số cụm (thành phần Gaussian); var = sigma^{-1}: phương sai đẳng hướng
        gamma: None -> dùng hàm cổng gamma(h~_t); số thực trong [0,1] -> gamma cố định
        tau: nhiệt độ Gumbel-softmax
        soft_transition: True -> đưa xác suất q(z_t) (mềm) vào LSTM chuyển trạng thái giống repo gốc;
                         False -> đưa mẫu Gumbel-softmax (lấy mẫu tổ tiên)
        """
        super().__init__()
        self.d, self.k, self.var, self.gamma_const, self.tau = d, k, var, gamma, tau
        self.soft_transition = soft_transition
        self.impute = PreImputation(d)
        # ---- mạng suy diễn q_phi (Eq. 10) ----
        self.enc = nn.LSTM(2 * d, hidden, batch_first=True)
        self.q_mlp = nn.Sequential(nn.Linear(hidden + k, hidden), nn.ReLU(), nn.Linear(hidden, k))
        self.gate = nn.Sequential(nn.Linear(hidden, hidden // 2), nn.ReLU(), nn.Linear(hidden // 2, 1))
        # ---- mạng sinh p_theta (Eq. 5) ----
        self.gen_cell = nn.LSTMCell(k, hidden)
        self.p_mlp = nn.Sequential(nn.Linear(hidden, hidden), nn.ReLU(), nn.Linear(hidden, k))
        # ---- hỗn hợp Gaussian cơ sở ----
        self.mu = nn.Parameter(torch.randn(k, d) * 0.5)          # tâm cụm mu_1..mu_k
        self.register_buffer("basis_prob", torch.full((k,), 1.0 / k))  # p(mu), Eq. (11)

    # ------------------------------------------------------------------ utils
    def init_mu_from_data(self, x, m):
        """Khởi tạo mu bằng các vector đặc trưng quan sát đầy đủ được chọn ngẫu nhiên."""
        full = m.reshape(-1, self.d).min(-1).values > 0
        pool = x.reshape(-1, self.d)[full]
        idx = torch.randperm(pool.shape[0])[: self.k]
        with torch.no_grad():
            self.mu.copy_(pool[idx] + 0.05 * torch.randn_like(pool[idx]))

    def log_px_given_z(self, x, m):
        """log p(x_t | z_t = c) cho mọi cụm c, chỉ tính trên phần quan sát được. -> (B,T,k)"""
        diff2 = (x[:, :, None, :] - self.mu[None, None]) ** 2                 # (B,T,k,d)
        ll = -0.5 * (diff2 / self.var + math.log(2 * math.pi * self.var))
        return (ll * m[:, :, None, :]).sum(-1)

    def gamma_t(self, h_enc):
        if self.gamma_const is not None:
            return torch.full(h_enc.shape[:-1] + (1,), float(self.gamma_const), device=h_enc.device)
        return torch.sigmoid(self.gate(h_enc))

    def filter(self, x, m, sample=True):
        """Chạy mạng suy diễn + mạng sinh trên đoạn quan sát.

        Trả về q (B,T,k), p (B,T,k) [p_1 = đều], gamma (B,T,1), trạng thái LSTM cuối.
        """
        B, T, _ = x.shape
        x_hat, _ = self.impute(x, m)
        x_in = m * x + (1 - m) * x_hat                        # đầu vào đã tiền nội suy
        h_enc, enc_state = self.enc(torch.cat([x_in, m], -1))
        z_prev = torch.zeros(B, self.k, device=x.device)      # z_0 = 0
        hg = (torch.zeros(B, self.gen_cell.hidden_size, device=x.device),) * 2
        qs, ps = [], []
        for t in range(T):
            if t == 0:
                p_t = torch.full((B, self.k), 1.0 / self.k, device=x.device)   # p(z_1) đều
            else:
                p_t = F.softmax(self.p_mlp(hg[0]), -1)                        # p(z_t | z_{1:t-1})
            logits = self.q_mlp(torch.cat([h_enc[:, t], z_prev], -1))
            q_t = F.softmax(logits, -1)                                       # q(z_t | x_{1:t}, z_{t-1})
            if sample and not self.soft_transition:
                z_t = F.gumbel_softmax(logits, tau=self.tau)                    # lấy mẫu tổ tiên
            else:
                z_t = q_t
            hg = self.gen_cell(z_t, hg)
            qs.append(q_t); ps.append(p_t); z_prev = z_t
        return {"q": torch.stack(qs, 1), "p": torch.stack(ps, 1), "gamma": self.gamma_t(h_enc),
                "x_in": x_in, "enc_state": enc_state, "gen_state": hg, "z_last": z_prev}

    # ------------------------------------------------------------------ ELBO
    def elbo(self, x, m, kl_weight=1.0):
        out = self.filter(x, m, sample=True)
        q, p, g = out["q"], out["p"], out["gamma"]
        logpx = self.log_px_given_z(x, m)                                     # (B,T,k)
        obs_t = (m.sum(-1, keepdim=True) > 0).float()                         # bước có quan sát

        # Eq. (11): ước lượng p(mu) = trung bình xác suất thành viên trên batch
        with torch.no_grad():
            batch_prob = (q * obs_t).sum((0, 1)) / obs_t.sum().clamp(min=1)
            self.basis_prob.mul_(0.9).add_(0.1 * batch_prob)
        pmu = self.basis_prob

        rec_dyn = ((1 - g) * (q * logpx).sum(-1, keepdim=True)).sum()          # số hạng 1
        rec_basis = (g * (pmu * logpx).sum(-1, keepdim=True)).sum()            # số hạng 4
        kl = (q * (torch.log(q + 1e-8) - torch.log(p + 1e-8))).sum()           # số hạng 2 + 3
        # chuẩn hoá như repo gốc: số hạng tái tạo chia cho số giá trị quan sát, KL chia cho số bước
        n, n_t = m.sum().clamp(min=1), float(m.shape[0] * m.shape[1])
        loss = -(rec_dyn + rec_basis) / n + kl_weight * kl / n_t
        return loss, {"rec": -(rec_dyn + rec_basis).item() / n.item(), "kl": kl.item() / n_t,
                           "gamma": g.mean().item()}

    # ------------------------------------------------------------------ forecast
    @torch.no_grad()
    def forecast(self, x, m, r, return_details=False):
        """Dự báo r bước: x~_{t+1} = sum_c psi_{t+1}[c] * mu_c,
        psi_{t+1} = (1-gamma) p(z_{t+1}|z_{1:t}) + gamma p(mu)     (Eq. 4)."""
        out = self.filter(x, m, sample=False)
        hg, (h, c) = out["gen_state"], out["enc_state"]
        h_last = h[-1]
        preds, psis, gammas, ps = [], [], [], []
        for _ in range(r):
            p_t = F.softmax(self.p_mlp(hg[0]), -1)
            g_t = self.gamma_t(h_last)
            psi = (1 - g_t) * p_t + g_t * self.basis_prob[None]
            x_t = psi @ self.mu
            preds.append(x_t); psis.append(psi); gammas.append(g_t); ps.append(p_t)
            # cập nhật: mạng sinh nhận z mềm, mạng suy diễn nhận giá trị vừa dự báo (mask = 1)
            hg = self.gen_cell(p_t, hg)
            inp = torch.cat([x_t, torch.ones_like(x_t)], -1)[:, None]
            o, (h, c) = self.enc(inp, (h, c))
            h_last = o[:, 0]
        pred = torch.stack(preds, 1)
        if not return_details:
            return pred
        return pred, {"q_past": out["q"], "gamma_past": out["gamma"], "x_in": out["x_in"],
                      "psi": torch.stack(psis, 1), "p_future": torch.stack(ps, 1),
                      "gamma_future": torch.stack(gammas, 1)}
