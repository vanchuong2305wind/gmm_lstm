"""Các mô hình so sánh.

- NaiveLast   : lặp lại giá trị quan sát cuối cùng của mỗi biến.
- GMMHMM      : HMM cổ điển với phát xạ Gaussian (tổng thể là một hỗn hợp Gaussian mà trọng số
                thay đổi theo chuỗi Markov) - "GMM + HMM", huấn luyện bằng EM (Baum-Welch).
- LSTMForecaster : mạng LSTM encoder-decoder, đầu vào nối [x, mask] như trong bài báo.
"""
import numpy as np
import torch
import torch.nn as nn
from hmmlearn.hmm import GaussianHMM


def forward_fill(x, m):
    """Điền giá trị thiếu bằng giá trị quan sát gần nhất trước đó (đầu chuỗi: 0 = trung bình)."""
    x, m = x.clone(), m.clone()
    last = torch.zeros(x.shape[0], x.shape[2])
    for t in range(x.shape[1]):
        last = torch.where(m[:, t] > 0, x[:, t], last)
        x[:, t] = last
    return x


class NaiveLast:
    def forecast(self, x, m, r):
        return forward_fill(x, m)[:, -1:].repeat(1, r, 1)


class GMMHMM:
    def __init__(self, k=20, n_iter=30, seed=0):
        self.hmm = GaussianHMM(n_components=k, covariance_type="diag", n_iter=n_iter,
                               random_state=seed, min_covar=1e-3)

    def fit(self, x, m):
        X = forward_fill(x, m).numpy()
        self.hmm.fit(X.reshape(-1, X.shape[-1]), lengths=[X.shape[1]] * X.shape[0])
        return self

    def forecast(self, x, m, r):
        X = forward_fill(x, m).numpy()
        A, mu = self.hmm.transmat_, self.hmm.means_
        out = np.zeros((X.shape[0], r, X.shape[-1]), dtype=np.float32)
        for b in range(X.shape[0]):
            # phân phối lọc P(s_w | x_{1:w}) = hàng cuối của posterior (thuật toán forward)
            pi = self.hmm.predict_proba(X[b])[-1]
            for h in range(r):
                pi = pi @ A                           # P(s_{w+h}) = P(s_w) A^h
                out[b, h] = pi @ mu                   # kỳ vọng của hỗn hợp Gaussian
        return torch.from_numpy(out)


class LSTMForecaster(nn.Module):
    def __init__(self, d, hidden=64):
        super().__init__()
        self.enc = nn.LSTM(2 * d, hidden, batch_first=True)
        self.dec = nn.LSTMCell(d, hidden)
        self.out = nn.Linear(hidden, d)

    def forecast(self, x, m, r):
        _, (h, c) = self.enc(torch.cat([x * m, m], -1))
        h, c = h[0], c[0]
        y = self.out(h)
        preds = []
        for _ in range(r):
            preds.append(y)
            h, c = self.dec(y, (h, c))
            y = self.out(h)
        return torch.stack(preds, 1)
