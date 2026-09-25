"""Sinh báo cáo Word: python build_report.py  ->  BaoCao_DGM2.docx"""
import json, os
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx_helpers import Report

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
RES = os.path.join(HERE, "..", "demo", "results")


def load(name):
    f = os.path.join(RES, name + ".json")
    return json.load(open(f, encoding="utf8")) if os.path.exists(f) else None


R = Report()
p, h, eq, fig, table, bullets = R.p, R.h, R.eq, R.fig, R.table, R.bullets

# =============================================================== TRANG BÌA
for txt, sz, b in [("[TÊN TRƯỜNG ĐẠI HỌC]", 14, True), ("[TÊN KHOA]", 13, True), ("", 12, False)]:
    par = R.doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = par.add_run(txt); r.font.size = Pt(sz); r.bold = b
for _ in range(3):
    R.doc.add_paragraph()
par = R.doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = par.add_run("BÁO CÁO GIỮA KỲ\nHỌC PHẦN: [TÊN HỌC PHẦN]".replace("\n", " – ")); r.font.size = Pt(14); r.bold = True
R.doc.add_paragraph()
par = R.doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = par.add_run("MÔ HÌNH HOÁ CHUỖI THỜI GIAN NHIỀU CHIỀU DỰA TRÊN HỖN HỢP GAUSSIAN ĐỘNG KẾT HỢP MẠNG NƠ-RON HỒI QUY")
r.font.size = Pt(18); r.bold = True
par = R.doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = par.add_run("Tìm hiểu mô hình DGM² (AAAI 2021) và demo ứng dụng dự báo khí hậu trên dữ liệu thưa USHCN")
r.font.size = Pt(14); r.italic = True
for _ in range(5):
    R.doc.add_paragraph()
for line in ["Giảng viên hướng dẫn: [Họ tên giảng viên]", "Sinh viên thực hiện: [Họ tên] – MSSV: [MSSV]",
             "Lớp: [Lớp]"]:
    par = R.doc.add_paragraph(); par.paragraph_format.left_indent = Cm(4)
    par.add_run(line).font.size = Pt(13)
for _ in range(5):
    R.doc.add_paragraph()
par = R.doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER
par.add_run("[Địa điểm], tháng 9/2026").italic = True
R.page_break()

# =============================================================== MỤC LỤC
par = R.doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = par.add_run("MỤC LỤC"); r.bold = True; r.font.size = Pt(16)
R.toc()
p("(Nếu mục lục chưa hiển thị: trong Word nhấn chuột phải vào vùng này → Update Field → Update entire table.)",
  align="center", size=10)
R.page_break()

# =============================================================== TÓM TẮT
par = R.doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = par.add_run("TÓM TẮT"); r.bold = True; r.font.size = Pt(16)
p("Báo cáo tìm hiểu lý thuyết mô hình hoá chuỗi thời gian nhiều chiều (multivariate time series – MTS) dựa trên "
  "mô hình hỗn hợp Gaussian (Gaussian Mixture Model – GMM) kết hợp với một mô hình chuỗi thời gian. Trọng tâm là "
  "mô hình **DGM²** (*Dynamic Gaussian Mixture based Deep Generative Model*) của Wu và cộng sự, công bố tại hội nghị "
  "AAAI 2021. DGM² giải quyết bài toán dự báo trên MTS **thưa** (nhiều giá trị bị thiếu) bằng cách không mô hình hoá "
  "trực tiếp từng vector đặc trưng $\\mathbf{x}_t$ riêng lẻ, mà mô hình hoá **sự chuyển dịch giữa các cụm tiềm ẩn** "
  "$z_t \\to z_{t+1}$ được chia sẻ giữa nhiều chuỗi. Các giá trị được sinh ra (phát xạ) từ một **phân phối hỗn hợp "
  "Gaussian động** mà trọng số thay đổi theo thời gian nhờ một mạng nơ-ron hồi quy (LSTM). Mô hình được huấn luyện "
  "bằng suy diễn biến phân với một mạng suy diễn có cấu trúc, thủ thuật Gumbel-softmax và một hàm cổng tự điều chỉnh.")
p("Để so sánh, báo cáo cũng trình bày cách tiếp cận cổ điển **GMM-HMM** (mô hình Markov ẩn với phát xạ Gaussian) – "
  "có thể xem là “tổ tiên” của DGM². Phần demo cài đặt lại DGM²-L bằng PyTorch, huấn luyện trên bộ dữ liệu khí hậu "
  "USHCN (được cung cấp trong mã nguồn của bài báo), so sánh với GMM-HMM, LSTM và phương pháp ngây thơ; đồng thời "
  "xây dựng một ứng dụng web tương tác (Streamlit) cho phép xem dự báo, xác suất cụm tiềm ẩn và hệ số cổng theo thời "
  "gian, cũng như thử nghiệm độ bền khi xoá bớt dữ liệu quan sát.")
p("**Từ khoá:** chuỗi thời gian nhiều chiều, dữ liệu thưa, mô hình hỗn hợp Gaussian, HMM, mô hình không gian trạng "
  "thái, suy diễn biến phân, LSTM, Gumbel-softmax, DGM².", indent=False)
R.page_break()

# =============================================================== CHƯƠNG 1
h("Chương 1. Giới thiệu")
h("1.1. Bối cảnh và động lực", 2)
p("Chuỗi thời gian nhiều chiều xuất hiện trong rất nhiều ứng dụng: giám sát hệ thống vật lý – mạng (cyber-physical "
  "systems), dự báo tài chính, phân tích giao thông, chẩn đoán lâm sàng, khí tượng… Một MTS ghi lại đồng thời $d$ biến "
  "theo thời gian; ví dụ với một bệnh nhân chạy thận nhân tạo, các biến có thể là áp lực tĩnh mạch, đường huyết, chỉ số "
  "tim–ngực (CTR)…")
p("Trong thực tế, dữ liệu này thường được **tích hợp từ nhiều nguồn không đồng nhất** với tần suất lấy mẫu khác nhau: "
  "xét nghiệm máu và chụp X-quang được thực hiện thưa hơn nhiều so với các lần lọc máu; các cảm biến trong một hệ thống "
  "lớn chạy trong những môi trường khác nhau; tin tức tài chính và giá cổ phiếu được ghi nhận ở các thời điểm không "
  "đồng bộ. Khi ghép tất cả lên một trục thời gian chung, ta thu được một MTS **rất thưa** – phần lớn ô dữ liệu bị thiếu. "
  "Ví dụ, bộ dữ liệu MIMIC-III trong bài báo có tỉ lệ thiếu tới 72,7%.")
p("Dữ liệu thưa làm phức tạp các phụ thuộc thời gian và khiến các mô hình phổ biến như mạng nơ-ron hồi quy (RNN) không "
  "dùng trực tiếp được. Cách làm phổ biến là **hai bước**: (1) nội suy (impute) giá trị thiếu, (2) dự báo trên dữ liệu "
  "đã nội suy. Tuy nhiên, cách này bỏ qua mối liên hệ giữa *mẫu hình thiếu* (missing pattern) và nhiệm vụ dự báo, nên "
  "cho kết quả kém khi độ thưa cao. Các phương pháp *end-to-end* gần đây (GRU-D, IPN, LGNet, Latent-ODE…) học đồng thời "
  "việc nội suy và dự báo, nhưng vẫn **xử lý từng chuỗi một cách riêng lẻ**, ít khai thác các cấu trúc ẩn được chia sẻ "
  "giữa nhiều chuỗi.")
fig(os.path.join(FIG, "fig1_latent_states.png"),
    "Minh hoạ cấu trúc tiềm ẩn phía sau MTS thưa của hai bệnh nhân lọc máu (Hình 1 trong bài báo). Mỗi thời điểm "
    "ứng với một trạng thái ẩn (khoẻ mạnh, rối loạn thận, thiếu máu); vector bên dưới mỗi trạng thái là đặc trưng thời "
    "gian được sinh từ một phân phối, ô trắng là giá trị bị thiếu. Các vector thuộc cùng một trạng thái – dù đến từ các "
    "bệnh nhân khác nhau – tạo thành một cụm trong không gian đặc trưng.", 11)
h("1.2. Ý tưởng chính của DGM²", 2)
p("Quan sát then chốt của bài báo: **các MTS không độc lập mà liên hệ với nhau qua các cấu trúc ẩn**. Trong suốt quá "
  "trình điều trị, mỗi bệnh nhân lần lượt trải qua các trạng thái tiềm ẩn như *rối loạn thận* hay *thiếu máu*, và các "
  "trạng thái này được “ngoại hiện” thành các chuỗi đo như đường huyết, albumin, tiểu cầu. Nếu hai bệnh nhân có tình "
  "trạng bệnh lý tương tự, một phần dữ liệu của họ được sinh ra từ cùng một mẫu trạng thái và tạo thành **cụm**. Tương tự, "
  "các trạm khí tượng gần nhau có thể cùng trải qua một kiểu thời tiết (trạng thái ẩn) chi phối nhiệt độ, lượng mưa…")
p("Do đó, thay vì mô hình hoá chuyển dịch $\\mathbf{x}_t \\to \\mathbf{x}_{t+1}$ của từng vector đặc trưng thưa, DGM² "
  "mô hình hoá chuyển dịch của **biến cụm tiềm ẩn** $z_t \\to z_{t+1}$. Vì mỗi cụm tổng hợp thông tin bổ sung cho nhau từ "
  "các đặc trưng tương tự thuộc nhiều chuỗi và nhiều thời điểm khác nhau, việc dựa vào cụm **bền vững hơn** nhiều so với "
  "dựa vào từng $\\mathbf{x}_t$ thưa. Cụ thể, DGM²:")
bullets([
    "là một **mô hình không gian trạng thái** (state space model) phi tuyến theo khuôn khổ *chuyển trạng thái – phát xạ* "
    "(transition – emission), trong đó các phân phối chuyển trạng thái được tham số hoá bằng mạng nơ-ron (RNN/LSTM hoặc ODE-RNN);",
    "đặc trưng bởi bước phát xạ dùng **phân phối hỗn hợp Gaussian động** – một GMM cơ sở tĩnh được “điều chỉnh” theo thời "
    "gian để nắm bắt động lực của cấu trúc cụm;",
    "dùng **suy diễn biến phân** với mạng suy diễn có cấu trúc để có thể suy diễn quy nạp (inductive) cho chuỗi mới;",
    "gắn **lớp tiền nội suy** tham số hoá ở đầu vào để suy diễn tin cậy trên dữ liệu thưa, và một **cơ chế cổng** để tự "
    "động điều chỉnh mức độ động của hỗn hợp Gaussian;",
    "xử lý được biến rời rạc (Gumbel-softmax) và **huấn luyện end-to-end** được.",
])
h("1.3. Mục tiêu và bố cục báo cáo", 2)
p("Đề bài yêu cầu tìm hiểu lý thuyết và trình bày demo một ứng dụng của mô hình hoá chuỗi thời gian nhiều chiều dựa "
  "trên GMM kết hợp với một mô hình chuỗi thời gian (HMM, DNN…). DGM² là một ví dụ tiêu biểu của hướng *GMM + DNN*, "
  "còn GMM-HMM là ví dụ kinh điển của hướng *GMM + HMM*; báo cáo trình bày cả hai và so sánh chúng. Bố cục:")
bullets([
    "**Chương 2** – Cơ sở lý thuyết: MTS thưa, GMM và thuật toán EM, HMM/GMM-HMM, RNN/LSTM, mô hình không gian trạng "
    "thái sâu, suy diễn biến phân – ELBO, Gumbel-softmax, nội suy bằng kernel.",
    "**Chương 3** – Mô hình DGM²: kiến trúc, lớp tiền nội suy, mô hình sinh với hỗn hợp Gaussian động, hàm mục tiêu, "
    "mạng suy diễn, cơ chế cổng, huấn luyện và dự báo; so sánh với GMM-HMM.",
    "**Chương 4** – Kết quả thực nghiệm được công bố trong bài báo.",
    "**Chương 5** – Demo: cài đặt lại DGM²-L, thí nghiệm trên USHCN và ứng dụng web tương tác.",
    "**Chương 6** – Kết luận và hướng phát triển.",
])

# =============================================================== CHƯƠNG 2
h("Chương 2. Cơ sở lý thuyết")
h("2.1. Chuỗi thời gian nhiều chiều thưa và bài toán dự báo", 2)
p("Theo khuôn khổ *nội suy – dự báo đồng thời* (Che et al. 2018; Shukla & Marlin 2019), một MTS thưa được biểu diễn "
  "với các ô thiếu trên một lưới các thời điểm tham chiếu cách đều $t = 1, \\dots, w$. Gọi")
eq(r"\mathbf{x}_{1:w} = (\mathbf{x}_1, \dots, \mathbf{x}_w) \in \mathbb{R}^{d \times w}, \qquad \mathbf{x}_t = (x^1_t, \dots, x^d_t)^\top \in \mathbb{R}^d", False)
p("là một MTS độ dài $w$, trong đó $\\mathbf{x}_t$ là **vector đặc trưng thời gian** tại bước $t$, $x^i_t$ là biến thứ "
  "$i$ và $d$ là số biến. Để đánh dấu các thời điểm có quan sát, ta dùng **mặt nạ nhị phân** "
  "$\\mathbf{m}_{1:w} \\in \\{0,1\\}^{d \\times w}$: $m^i_t = 1$ nếu $x^i_t$ được quan sát, ngược lại $m^i_t = 0$ và $x^i_t$ "
  "chỉ là giá trị giữ chỗ (NaN). **Tỉ lệ thiếu** là tỉ lệ các ô có $m^i_t = 0$.")
p("Bài toán **dự báo trên MTS thưa**: ước lượng chuỗi $r$ bước tương lai có khả năng cao nhất khi biết quá khứ *không "
  "đầy đủ* trong $w$ bước:")
eq(r"\tilde{\mathbf{x}}_{w+1:w+r} = \arg\max_{\mathbf{x}_{w+1:w+r}} \; p(\mathbf{x}_{w+1:w+r} \mid \mathbf{x}_{1:w}, \mathbf{m}_{1:w})")
p("trong đó $p(\\cdot \\mid \\cdot)$ là hàm dự báo cần học. Với mô hình xác suất, thay cho arg max ta thường dùng **kỳ "
  "vọng** của phân phối dự báo làm giá trị dự báo điểm, vì nó tối ưu sai số bình phương trung bình (RMSE).")

h("2.2. Mô hình hỗn hợp Gaussian (GMM)", 2)
h("2.2.1. Định nghĩa", 3)
p("GMM mô hình hoá mật độ của một vector $\\mathbf{x} \\in \\mathbb{R}^d$ như tổ hợp lồi của $k$ phân phối Gaussian:")
eq(r"p(\mathbf{x}) = \sum_{c=1}^{k} \pi_c \, \mathcal{N}(\mathbf{x} \mid \boldsymbol{\mu}_c, \boldsymbol{\Sigma}_c), \qquad \pi_c \ge 0, \;\; \sum_{c=1}^{k} \pi_c = 1")
p("với $\\pi_c$ là **trọng số (xác suất) trộn**, $\\boldsymbol{\\mu}_c$ và $\\boldsymbol{\\Sigma}_c$ là trung bình và ma "
  "trận hiệp phương sai của thành phần thứ $c$, và mật độ Gaussian nhiều chiều")
eq(r"\mathcal{N}(\mathbf{x} \mid \boldsymbol{\mu}, \boldsymbol{\Sigma}) = \frac{1}{(2\pi)^{d/2} |\boldsymbol{\Sigma}|^{1/2}} \exp\left( -\frac{1}{2} (\mathbf{x} - \boldsymbol{\mu})^\top \boldsymbol{\Sigma}^{-1} (\mathbf{x} - \boldsymbol{\mu}) \right)")
p("GMM có cách diễn giải **sinh dữ liệu** với một biến ẩn rời rạc $z \\in \\{1,\\dots,k\\}$ cho biết điểm dữ liệu thuộc "
  "cụm nào: (1) rút $z \\sim \\mathrm{Categorical}(\\boldsymbol{\\pi})$; (2) rút $\\mathbf{x} \\sim \\mathcal{N}(\\boldsymbol{\\mu}_z, "
  "\\boldsymbol{\\Sigma}_z)$. Lấy biên theo $z$ ta được lại công thức (2). Xác suất hậu nghiệm để $\\mathbf{x}$ thuộc cụm $c$ "
  "(gọi là **độ trách nhiệm** – responsibility) theo định lý Bayes:")
eq(r"r_c(\mathbf{x}) = p(z = c \mid \mathbf{x}) = \frac{\pi_c \, \mathcal{N}(\mathbf{x} \mid \boldsymbol{\mu}_c, \boldsymbol{\Sigma}_c)}{\sum_{c'=1}^{k} \pi_{c'} \, \mathcal{N}(\mathbf{x} \mid \boldsymbol{\mu}_{c'}, \boldsymbol{\Sigma}_{c'})}")
p("Như vậy GMM vừa là một bộ **ước lượng mật độ** linh hoạt (xấp xỉ được mọi mật độ liên tục khi $k$ đủ lớn), vừa là "
  "một phương pháp **phân cụm mềm**. Trường hợp đặc biệt được DGM² sử dụng là Gaussian **đẳng hướng** "
  "$\\boldsymbol{\\Sigma}_c = \\sigma^{-1}\\mathbf{I}$ với cùng một phương sai cho mọi thành phần, khi đó "
  "$\\log \\mathcal{N}(\\mathbf{x} \\mid \\boldsymbol{\\mu}_c, \\sigma^{-1}\\mathbf{I}) = -\\frac{\\sigma}{2}\\|\\mathbf{x} - "
  "\\boldsymbol{\\mu}_c\\|^2 + \\text{const}$, tức log-likelihood tỉ lệ nghịch với khoảng cách Euclid đến tâm cụm – "
  "rất gần với k-means.")
h("2.2.2. Ước lượng tham số bằng thuật toán EM", 3)
p("Với tập dữ liệu $\\{\\mathbf{x}_n\\}_{n=1}^{N}$ độc lập, log-likelihood "
  "$\\sum_n \\log \\sum_c \\pi_c \\mathcal{N}(\\mathbf{x}_n \\mid \\boldsymbol{\\mu}_c, \\boldsymbol{\\Sigma}_c)$ có tổng nằm trong "
  "log nên không có nghiệm dạng đóng. Thuật toán **Expectation–Maximization (EM)** lặp hai bước:")
bullets([
    "**Bước E:** tính độ trách nhiệm $r_{nc} = p(z_n = c \\mid \\mathbf{x}_n)$ theo (4) với tham số hiện tại.",
    "**Bước M:** cập nhật $N_c = \\sum_n r_{nc}$, $\\pi_c = N_c / N$, $\\boldsymbol{\\mu}_c = \\frac{1}{N_c}\\sum_n r_{nc}\\mathbf{x}_n$, "
    "$\\boldsymbol{\\Sigma}_c = \\frac{1}{N_c}\\sum_n r_{nc}(\\mathbf{x}_n - \\boldsymbol{\\mu}_c)(\\mathbf{x}_n - \\boldsymbol{\\mu}_c)^\\top$.",
])
p("Mỗi vòng lặp EM đảm bảo không làm giảm log-likelihood. Về bản chất, EM là cực đại hoá một **cận dưới** của "
  "log-likelihood thu được từ bất đẳng thức Jensen – đúng là ý tưởng mà suy diễn biến phân (mục 2.6) tổng quát hoá.")
h("2.2.3. Hạn chế của GMM với chuỗi thời gian", 3)
p("GMM chuẩn giả định các điểm dữ liệu **độc lập, cùng phân phối** và trọng số trộn $\\boldsymbol{\\pi}$ là **tĩnh**. Với "
  "chuỗi thời gian, cụm mà $\\mathbf{x}_{t+1}$ thuộc về rõ ràng phụ thuộc vào lịch sử (ví dụ bệnh nhân đang ở trạng thái "
  "“rối loạn thận” thì nhiều khả năng bước sau vẫn ở trạng thái đó). Vì vậy cần kết hợp GMM với một mô hình động học "
  "trên biến cụm – đó là ý tưởng của HMM (động học Markov) và của DGM² (động học do RNN học).")

h("2.3. Mô hình Markov ẩn (HMM) và GMM-HMM", 2)
p("HMM là mô hình không gian trạng thái với trạng thái ẩn rời rạc $s_t \\in \\{1,\\dots,k\\}$. Tham số gồm: phân phối ban "
  "đầu $\\pi_c = p(s_1 = c)$, **ma trận chuyển** $A_{cc'} = p(s_{t+1} = c' \\mid s_t = c)$ và **phân phối phát xạ** "
  "$p(\\mathbf{x}_t \\mid s_t = c) = \\mathcal{N}(\\mathbf{x}_t \\mid \\boldsymbol{\\mu}_c, \\boldsymbol{\\Sigma}_c)$ (HMM Gaussian; nếu "
  "mỗi trạng thái lại là một GMM ta có GMM-HMM theo nghĩa hẹp, thường dùng trong nhận dạng tiếng nói). Phân phối đồng thời:")
eq(r"p(\mathbf{x}_{1:T}, s_{1:T}) = p(s_1) \prod_{t=1}^{T-1} p(s_{t+1} \mid s_t) \prod_{t=1}^{T} p(\mathbf{x}_t \mid s_t)")
p("Điểm đáng chú ý: **phân phối biên của $\\mathbf{x}_t$ tại mỗi thời điểm là một GMM** với trọng số trộn "
  "$p(s_t = c \\mid \\mathbf{x}_{1:t-1})$ thay đổi theo thời gian – tức HMM Gaussian chính là một “hỗn hợp Gaussian động” "
  "dạng đơn giản, trong đó động học của trọng số là xích Markov bậc nhất tuyến tính.")
p("**Thuật toán forward** tính xác suất lọc $\\alpha_t(c) = p(\\mathbf{x}_{1:t}, s_t = c)$ một cách đệ quy:")
eq(r"\alpha_1(c) = \pi_c \, p(\mathbf{x}_1 \mid s_1 = c)")
eq(r"\alpha_{t+1}(c') = p(\mathbf{x}_{t+1} \mid s_{t+1} = c') \sum_{c=1}^{k} \alpha_t(c) A_{cc'}", False)
p("với độ phức tạp $O(Tk^2)$. Tham số được học bằng **Baum–Welch** (EM cho HMM, dùng thêm thuật toán backward). Để "
  "**dự báo** $h$ bước, ta chuẩn hoá $\\alpha_w$ thành phân phối lọc $\\boldsymbol{\\pi}_w = p(s_w \\mid \\mathbf{x}_{1:w})$ rồi "
  "lan truyền qua ma trận chuyển:")
eq(r"p(s_{w+h} \mid \mathbf{x}_{1:w}) = \boldsymbol{\pi}_w^\top A^h, \qquad \hat{\mathbf{x}}_{w+h} = \sum_{c=1}^{k} p(s_{w+h} = c \mid \mathbf{x}_{1:w}) \, \boldsymbol{\mu}_c")
p("**Hạn chế:** (i) giả định Markov bậc nhất – trạng thái kế tiếp chỉ phụ thuộc trạng thái hiện tại, không nhớ được phụ "
  "thuộc dài hạn; (ii) động học tuyến tính trong không gian xác suất ($A^h$ hội tụ nhanh về phân phối dừng nên dự báo xa "
  "tiến về trung bình); (iii) không có cơ chế tự nhiên cho dữ liệu thiếu kiểu *một phần* vector (phải nội suy trước); "
  "(iv) mỗi trạng thái có tham số riêng, số tham số tăng nhanh theo $k$ và $d$. DGM² khắc phục (i), (ii) bằng RNN và (iii) "
  "bằng mặt nạ và lớp tiền nội suy.")

h("2.4. Mạng nơ-ron hồi quy và LSTM", 2)
p("RNN xử lý chuỗi bằng một trạng thái ẩn $\\mathbf{h}_t = f(\\mathbf{h}_{t-1}, \\mathbf{u}_t)$ cập nhật tuần tự, về lý "
  "thuyết mang thông tin của toàn bộ lịch sử $\\mathbf{u}_{1:t}$. **LSTM** (Long Short-Term Memory) bổ sung ô nhớ "
  "$\\mathbf{c}_t$ và các cổng để giảm hiện tượng tiêu biến gradient:")
eq(r"\mathbf{i}_t = \sigma(W_i[\mathbf{h}_{t-1}, \mathbf{u}_t] + b_i), \quad \mathbf{f}_t = \sigma(W_f[\mathbf{h}_{t-1}, \mathbf{u}_t] + b_f)")
eq(r"\mathbf{o}_t = \sigma(W_o[\mathbf{h}_{t-1}, \mathbf{u}_t] + b_o)", False)
eq(r"\mathbf{c}_t = \mathbf{f}_t \odot \mathbf{c}_{t-1} + \mathbf{i}_t \odot \tanh(W_c[\mathbf{h}_{t-1}, \mathbf{u}_t] + b_c), \qquad \mathbf{h}_t = \mathbf{o}_t \odot \tanh(\mathbf{c}_t)")
p("Trong DGM², LSTM (hoặc GRU, hoặc ODE-RNN) được dùng ở hai chỗ: làm **hàm chuyển trạng thái** trên chuỗi biến cụm "
  "trong mô hình sinh, và làm **bộ mã hoá** trong mạng suy diễn. Biến thể **ODE-RNN** (Rubanova et al. 2019) cho trạng thái "
  "ẩn tiến hoá liên tục theo một phương trình vi phân thường $d\\mathbf{h}/dt = f_\\theta(\\mathbf{h})$ giữa các lần quan "
  "sát, phù hợp khi các bước thời gian không đều (DGM²-O).")

h("2.5. Mô hình không gian trạng thái sâu (Deep Markov Model)", 2)
p("Mô hình không gian trạng thái (SSM) mô tả chuỗi quan sát qua hai quá trình: **chuyển trạng thái** "
  "$p(z_{t+1} \\mid z_{1:t})$ và **phát xạ** $p(\\mathbf{x}_t \\mid z_t)$. HMM và bộ lọc Kalman là các SSM kinh điển với giả "
  "định tuyến tính / Markov. **Deep Markov Model** (DMM, Krishnan et al. 2017) thay các phân phối này bằng mạng nơ-ron "
  "(trạng thái ẩn liên tục Gaussian) và dùng một **mạng suy diễn có cấu trúc** "
  "$q(z_{1:T} \\mid \\mathbf{x}_{1:T}) = q(z_1 \\mid \\mathbf{x}) \\prod_t q(z_{t+1} \\mid z_t, \\mathbf{x})$ – phản ánh cấu trúc "
  "Markov của hậu nghiệm thật – để huấn luyện bằng ELBO. DGM² kế thừa trực tiếp khuôn khổ này nhưng với **trạng thái "
  "rời rạc = cụm** và **phát xạ là hỗn hợp Gaussian động**.")

h("2.6. Suy diễn biến phân và cận dưới ELBO", 2)
p("Với mô hình biến ẩn $p_\\vartheta(\\mathbf{x}, \\mathbf{z})$, ta muốn cực đại log-likelihood biên "
  "$\\log p_\\vartheta(\\mathbf{x}) = \\log \\sum_{\\mathbf{z}} p_\\vartheta(\\mathbf{x}, \\mathbf{z})$. Khi $\\mathbf{z}$ là một chuỗi "
  "gồm $w$ biến rời rạc $k$ giá trị, tổng có $k^w$ số hạng và hậu nghiệm $p(\\mathbf{z} \\mid \\mathbf{x})$ khó tính "
  "(intractable) nếu chuyển trạng thái là RNN phi tuyến. Suy diễn biến phân đưa vào một phân phối xấp xỉ "
  "$q_\\phi(\\mathbf{z} \\mid \\mathbf{x})$ và dùng bất đẳng thức Jensen ($\\log$ là hàm lõm):")
eq(r"\log p_\vartheta(\mathbf{x}) = \log \mathbb{E}_{q_\phi(\mathbf{z}|\mathbf{x})}\left[\frac{p_\vartheta(\mathbf{x}, \mathbf{z})}{q_\phi(\mathbf{z}|\mathbf{x})}\right] \ge \mathbb{E}_{q_\phi(\mathbf{z}|\mathbf{x})}\left[\log \frac{p_\vartheta(\mathbf{x}, \mathbf{z})}{q_\phi(\mathbf{z}|\mathbf{x})}\right]")
eq(r"= \mathbb{E}_{q_\phi}\left[\log p_\vartheta(\mathbf{x}|\mathbf{z})\right] - \mathcal{D}_{KL}\left(q_\phi(\mathbf{z}|\mathbf{x}) \,\|\, p_\vartheta(\mathbf{z})\right) = \ell(\vartheta, \phi)", False)
p("$\\ell$ gọi là **ELBO** (evidence lower bound). Có thể chứng minh "
  "$\\log p_\\vartheta(\\mathbf{x}) - \\ell = \\mathcal{D}_{KL}(q_\\phi(\\mathbf{z}|\\mathbf{x}) \\| p_\\vartheta(\\mathbf{z}|\\mathbf{x})) \\ge 0$, "
  "nên cực đại ELBO theo $\\phi$ làm $q$ tiến gần hậu nghiệm thật, còn theo $\\vartheta$ làm tăng likelihood. ELBO gồm hai "
  "phần: **số hạng tái tạo** (mô hình giải thích dữ liệu tốt đến đâu) và **số hạng KL** (điều chuẩn, giữ hậu nghiệm gần "
  "tiên nghiệm – giúp chống quá khớp như trong VAE). Khi $q_\\phi$ được tham số hoá bằng một mạng nơ-ron nhận $\\mathbf{x}$ "
  "làm đầu vào (*amortized inference*), mô hình suy diễn được ngay cho chuỗi mới chưa thấy khi huấn luyện – tính "
  "**quy nạp** (inductive). Trong thực hành thường nhân số hạng KL với hệ số $\\beta$ tăng dần từ 0 (**KL annealing**) để "
  "tránh hậu nghiệm bị “sập” về tiên nghiệm ở đầu quá trình huấn luyện.")

h("2.7. Thủ thuật Gumbel-softmax", 2)
p("Để tối ưu ELBO bằng gradient khi $z$ rời rạc, cần lấy mẫu $z \\sim \\mathrm{Categorical}(\\boldsymbol{\\pi})$ theo cách "
  "khả vi. Gumbel-max cho biết $z = \\arg\\max_c (\\log \\pi_c + g_c)$ với $g_c = -\\log(-\\log u_c)$, $u_c \\sim U(0,1)$ là một "
  "mẫu đúng. Gumbel-softmax (Jang et al. 2017) thay arg max bằng softmax có nhiệt độ $\\tau$:")
eq(r"y_c = \frac{\exp\left((\log \pi_c + g_c)/\tau\right)}{\sum_{c'=1}^{k} \exp\left((\log \pi_{c'} + g_{c'})/\tau\right)}")
p("$\\mathbf{y}$ là vector trên đơn hình, tiến tới one-hot khi $\\tau \\to 0$, và khả vi theo $\\boldsymbol{\\pi}$ – cho phép "
  "lan truyền ngược qua bước “lấy mẫu” trong mạng suy diễn của DGM².")

h("2.8. Nội suy bằng kernel và hàm cường độ", 2)
p("Mạng Interpolation-Prediction (IPN, Shukla & Marlin 2019) nội suy chuỗi thưa lên lưới thời gian tham chiếu bằng "
  "**trung bình có trọng số kernel** của các quan sát lân cận, trong đó tổng các trọng số – **hàm cường độ** $\\lambda$ – "
  "cho biết mật độ quan sát quanh thời điểm đó (độ tin cậy của giá trị nội suy). Các tham số của kernel được học cùng mô "
  "hình dự báo, nên cách nội suy được “căn chỉnh” theo nhiệm vụ. DGM² kế thừa ý tưởng này ở lớp tiền nội suy (mục 3.2).")

# =============================================================== CHƯƠNG 3
h("Chương 3. Mô hình DGM²")
h("3.1. Tổng quan kiến trúc", 2)
p("DGM² gồm hai khối được huấn luyện đồng thời (end-to-end):")
bullets([
    "**Lớp tiền nội suy** (pre-imputation layer): ước lượng các ô thiếu bằng cách khai thác (1) xu hướng trơn và cường độ "
    "quan sát theo thời gian và (2) tương quan giữa các biến.",
    "**Khối dự báo** (forecasting component): một mô hình sinh sâu ước lượng phân phối động của cấu trúc cụm tiềm ẩn, gồm "
    "*mạng sinh* $p_\\vartheta$ (Hình 2b) và *mạng suy diễn* $q_\\phi$ (Hình 2c).",
])
fig(os.path.join(FIG, "fig2_architecture.png"),
    "(a) Điều chỉnh động hỗn hợp Gaussian theo công thức (17) với hai thành phần; (b) mạng sinh; (c) mạng suy diễn, trong "
    "đó $\\gamma(\\cdot)$ là hàm cổng (Hình 2 trong bài báo).", 16)

h("3.2. Lớp tiền nội suy", 2)
p("Với biến thứ $i$ tại thời điểm tham chiếu $t^*$, dùng **kernel Gaussian** để đánh giá ảnh hưởng của mỗi bước "
  "$t$ ($1 \\le t \\le w$) lên $t^*$:")
eq(r"\kappa(t^*, t; \alpha_i) = e^{-\alpha_i (t^* - t)^2}")
p("trong đó $\\alpha_i > 0$ là tham số học được (điều khiển độ rộng kernel riêng cho từng biến: biến thay đổi chậm như "
  "nhiệt độ có thể dùng kernel rộng, biến biến động mạnh như lượng mưa dùng kernel hẹp). Ước lượng $x^i_{t^*}$ bằng "
  "trung bình có trọng số:")
eq(r"\bar{x}^i_{t^*} = \frac{1}{\lambda(t^*, \mathbf{m}^i; \alpha_i)} \sum_{t=1}^{w} \kappa(t^*, t; \alpha_i) \, m^i_t \, x^i_t")
eq(r"\lambda(t^*, \mathbf{m}^i; \alpha_i) = \sum_{t=1}^{w} m^i_t \, \kappa(t^*, t; \alpha_i)", False)
p("$\\mathbf{m}^i = (m^i_1, \\dots, m^i_w)^\\top$ là mặt nạ của biến $i$, dùng để loại các bước không quan sát; "
  "$\\lambda$ là **hàm cường độ** đo mật độ quan sát quanh $t^*$. Để tận dụng **tương quan giữa các biến**, DGM² đưa "
  "vào các hệ số tương quan học được $\\rho_{ij}$ ($\\rho_{ii} = 1$) và kết hợp thông tin từ $d$ biến khi $x^i_{t^*}$ bị thiếu:")
eq(r"\hat{x}^i_{t^*} = \left[ \sum_{j=1}^{d} \rho_{ij} \, \lambda(t^*, \mathbf{m}^i; \alpha_j) \, \bar{x}^j_{t^*} \right] \Big/ \sum_{j'=1}^{d} \lambda(t^*, \mathbf{m}^i; \alpha_{j'})")
p("Thừa số $\\lambda(\\cdot; \\alpha_j)$ đóng vai trò **độ tin cậy** của $\\bar{x}^j_{t^*}$: $\\lambda$ càng lớn thì càng có "
  "nhiều quan sát gần $\\bar{x}^j_{t^*}$. Tập tham số của lớp là $\\boldsymbol{\\alpha} = [\\alpha_1, \\dots, \\alpha_d]$ và "
  "$\\boldsymbol{\\rho} = [\\rho_{ij}] \\in \\mathbb{R}^{d \\times d}$; chúng được huấn luyện cùng mô hình sinh, nhờ đó mẫu hình "
  "thiếu được căn chỉnh theo nhiệm vụ dự báo. Đầu vào cho khối dự báo là "
  "$\\mathbf{m}_t \\odot \\mathbf{x}_t + (1 - \\mathbf{m}_t) \\odot \\hat{\\mathbf{x}}_t$ – giữ nguyên giá trị quan sát, chỉ thay các ô thiếu.")

h("3.3. Mô hình sinh với hỗn hợp Gaussian động", 2)
h("3.3.1. Biến cụm tiềm ẩn và chuyển trạng thái", 3)
p("Giả sử có $k$ cụm tiềm ẩn chung cho **mọi** vector đặc trưng $\\mathbf{x}_t$ trong một batch các MTS. Với mỗi bước $t$, "
  "gắn $\\mathbf{x}_t$ với một **biến cụm** $z_t \\in \\{1, \\dots, k\\}$. Quá trình chuyển trạng thái dùng cấu trúc hồi quy vì "
  "khả năng mô hình hoá phụ thuộc dài hạn: xác suất trạng thái mới $z_{t+1}$ được cập nhật dựa trên **toàn bộ** các trạng "
  "thái trước $z_{1:t}$ (khác với HMM chỉ dựa trên $z_t$):")
eq(r"p(z_{t+1} \mid z_{1:t}) = f_\theta(z_{1:t})")
p("với $f_\\theta$ được tham số hoá bằng một RNN:")
eq(r"p(z_{t+1} \mid z_{1:t}) = \mathrm{softmax}\left(\mathrm{MLP}(\mathbf{h}_t)\right), \qquad \mathbf{h}_t = \mathrm{RNN}(z_t, \mathbf{h}_{t-1})")
p("trong đó RNN có thể là LSTM/GRU (**DGM²-L**) hoặc ODE-RNN (**DGM²-O**) để xử lý các bước thời gian không đều.")
h("3.3.2. Phát xạ từ hỗn hợp Gaussian động", 3)
p("Gọi $\\boldsymbol{\\mu}_c$ ($c = 1..k$) là tâm của thành phần thứ $c$ trong một **hỗn hợp cơ sở** tĩnh và $p(\\boldsymbol{\\mu}_c)$ "
  "là xác suất trộn tương ứng. Phát xạ vector mới $\\mathbf{x}_{t+1}$ gồm hai bước: (1) rút biến cụm $z_{t+1}$ từ một phân phối "
  "categorical trên các thành phần; (2) rút $\\mathbf{x}_{t+1} \\sim \\mathcal{N}(\\boldsymbol{\\mu}_{z_{t+1}}, \\sigma^{-1}\\mathbf{I})$ – "
  "Gaussian đẳng hướng với $\\sigma$ là siêu tham số (chọn vì hiệu quả tính toán và hiệu quả thực nghiệm).")
p("Nếu ở bước (1) dùng phân phối tĩnh $p(\\boldsymbol{\\mu}) = [p(\\boldsymbol{\\mu}_1), \\dots, p(\\boldsymbol{\\mu}_k)]$ như GMM "
  "thông thường thì không phản ánh được động lực của MTS. Vì xác suất chuyển $p(z_{t+1} \\mid z_{1:t})$ cho biết "
  "$\\mathbf{x}_{t+1}$ nhiều khả năng thuộc cụm nào, DGM² **điều chỉnh động** xác suất trộn tại mỗi bước:")
eq(r"\boldsymbol{\psi}_{t+1} = (1 - \gamma) \, p(z_{t+1} \mid z_{1:t}) + \gamma \, p(\boldsymbol{\mu})")
p("$\\boldsymbol{\\psi}_{t+1}$ là **phân phối hỗn hợp động** tại bước $t+1$; số hạng thứ nhất là *điều chỉnh động*, số hạng "
  "thứ hai là *hỗn hợp cơ sở*; $\\gamma \\in [0,1]$ điều khiển mức độ lệch khỏi hỗn hợp cơ sở. Hình 2(a) minh hoạ: "
  "$p(z_{t+1} \\mid z_{1:t})$ “kéo” hỗn hợp về phía thành phần (cụm) mà $\\mathbf{x}_{t+1}$ thuộc về. Việc giữ lại hỗn hợp cơ "
  "sở là **không thể thiếu** vì nó xác định quan hệ giữa các thành phần và điều chuẩn việc học các tâm "
  "$\\boldsymbol{\\mu} = [\\boldsymbol{\\mu}_1, \\dots, \\boldsymbol{\\mu}_k]$. Mật độ phát xạ tổng thể tại bước $t+1$ vì vậy là một GMM có "
  "trọng số thay đổi theo thời gian:")
eq(r"p(\mathbf{x}_{t+1} \mid z_{1:t}) = \sum_{c=1}^{k} \psi_{t+1}[c] \; \mathcal{N}(\mathbf{x}_{t+1} \mid \boldsymbol{\mu}_c, \sigma^{-1}\mathbf{I})")
h("3.3.3. Quá trình sinh", 3)
p("Tóm lại, quá trình sinh của DGM² với mỗi MTS là:", indent=False)
R.numbered([
    "Rút $z_1 \\sim \\mathrm{Uniform}(k)$.",
    "Với $t = 1, \\dots, w$: (i) tính xác suất chuyển $p(z_{t+1} \\mid z_{1:t}) = f_\\theta(z_{1:t})$; (ii) rút "
    "$z_{t+1} \\sim \\mathrm{Categorical}(p(z_{t+1} \\mid z_{1:t}))$ cho **chuyển trạng thái**; (iii) rút "
    "$\\tilde{z}_{t+1} \\sim \\mathrm{Categorical}(\\boldsymbol{\\psi}_{t+1})$ theo (17) cho **phát xạ**; (iv) rút vector đặc trưng "
    "$\\tilde{\\mathbf{x}}_{t+1} \\sim \\mathcal{N}(\\boldsymbol{\\mu}_{\\tilde{z}_{t+1}}, \\sigma^{-1}\\mathbf{I})$.",
])
p("Lưu ý $z_{t+1}$ (bước ii) và $\\tilde{z}_{t+1}$ (bước iii) khác nhau: $z_{t+1}$ dùng để duy trì tính hồi quy của chuỗi "
  "chuyển trạng thái, còn $\\tilde{z}_{t+1}$ dùng cho phát xạ từ hỗn hợp đã cập nhật. Các tham số $\\boldsymbol{\\mu}_c$ được "
  "**chia sẻ bởi mọi mẫu thuộc cùng cụm** – ở mọi chuỗi và mọi thời điểm – nhờ đó hợp nhất thông tin bổ sung cho nhau, "
  "giúp dự báo bền vững trên dữ liệu thưa. Tập tham số của mô hình sinh là $\\vartheta = \\{\\theta, \\boldsymbol{\\mu}\\}$.")

h("3.4. Hàm mục tiêu và cận dưới Jensen", 2)
p("Mục tiêu là cực đại log-likelihood biên của mỗi MTS:")
eq(r"\mathcal{L}(\vartheta) = \log \sum_{z_{1:w}} p_\vartheta(\mathbf{x}_{1:w}, z_{1:w})")
p("Phân tích xác suất đồng thời theo hỗn hợp động (17) và áp dụng bất đẳng thức Jensen cho từng bước, ta được cận dưới:")
eq(r"\mathcal{L}(\vartheta) \ge \sum_{t=0}^{w-1} \sum_{z_{1:t+1}} \left[ \log p_\vartheta(\mathbf{x}_{t+1} \mid z_{t+1}) \right] p_\theta(z_{1:t}) \, \times")
eq(r"\left[ (1-\gamma) \, p_\theta(z_{t+1} \mid z_{1:t}) + \gamma \, p(\boldsymbol{\mu}_{z_{t+1}}) \right]", False)
p("*Phác thảo lập luận:* theo quá trình sinh, "
  "$p(\\mathbf{x}_{t+1} \\mid z_{1:t}) = \\sum_{c} \\psi_{t+1}[c] \\, p(\\mathbf{x}_{t+1} \\mid z_{t+1} = c)$. Vì $\\boldsymbol{\\psi}_{t+1}$ là "
  "một phân phối xác suất và $\\log$ lõm, Jensen cho "
  "$\\log \\sum_c \\psi_{t+1}[c] \\, p(\\mathbf{x}_{t+1} \\mid c) \\ge \\sum_c \\psi_{t+1}[c] \\log p(\\mathbf{x}_{t+1} \\mid c)$; lấy kỳ vọng "
  "theo lịch sử $z_{1:t}$ và cộng qua các bước ta được (20). Cận này có ý nghĩa trực quan: log-likelihood của mỗi quan sát "
  "được **tính trung bình theo trọng số của hỗn hợp động** – vừa theo dự đoán động $p_\\theta(z_{t+1} \\mid z_{1:t})$, vừa theo "
  "hỗn hợp cơ sở $p(\\boldsymbol{\\mu})$.")
p("Tuy nhiên việc lấy tổng theo mọi chuỗi $z_{1:t+1}$ ($k^{t+1}$ khả năng) là không khả thi, và hậu nghiệm thật "
  "$p(\\mathbf{z} \\mid \\mathbf{x}_{1:w})$ không tính được vì chuyển trạng thái là RNN phi tuyến. Để vượt qua, đồng thời cho "
  "phép suy diễn quy nạp, DGM² dùng suy diễn biến phân với một mạng suy diễn.")

h("3.5. Mạng suy diễn có cấu trúc và ELBO", 2)
p("DGM² đưa vào hậu nghiệm xấp xỉ $q_\\phi(\\mathbf{z} \\mid \\mathbf{x}_{1:w})$ tham số hoá bởi mạng nơ-ron với tham số $\\phi$. "
  "Mạng suy diễn được thiết kế **có cấu trúc** theo ý tưởng quá trình Markov sâu để duy trì phụ thuộc thời gian giữa các "
  "biến ẩn:")
eq(r"q_\phi(\mathbf{z} \mid \mathbf{x}_{1:w}) = q_\phi(z_1 \mid \mathbf{x}_1) \prod_{t=1}^{w-1} q_\phi(z_{t+1} \mid \mathbf{x}_{1:t+1}, z_t)")
p("Mỗi thừa số là một cấu trúc hồi quy (Hình 2c):")
eq(r"q_\phi(z_{t+1} \mid \mathbf{x}_{1:t+1}, z_t) = \mathrm{softmax}\left(\mathrm{MLP}(\tilde{\mathbf{h}}_{t+1})\right), \qquad \tilde{\mathbf{h}}_{t+1} = \mathrm{RNN}(\mathbf{x}_t, \tilde{\mathbf{h}}_t)")
p("với $\\tilde{\\mathbf{h}}_t$ là trạng thái ẩn thứ $t$ của RNN suy diễn, $z_0 = \\mathbf{0}$ để không ảnh hưởng đến vòng lặp; "
  "MLP nhận cả $\\tilde{\\mathbf{h}}_{t+1}$ và mẫu $z_t$ của bước trước (mũi tên từ $z_{t-1}$ vào MLP trong Hình 2c). Kết hợp "
  "với bước chặn (20), ta được **ELBO** của DGM² $\\ell(\\vartheta, \\phi) \\le \\mathcal{L}(\\vartheta)$:")
eq(r"\ell(\vartheta, \phi) = (1-\gamma) \sum_{t=1}^{w} \mathbb{E}_{q_\phi(z_t|\mathbf{x}_{1:t})}\left[\log p_\vartheta(\mathbf{x}_t \mid z_t)\right]")
eq(r"- \sum_{t=1}^{w-1} \mathbb{E}_{q_\phi(z_{1:t}|\mathbf{x}_{1:t})}\left[ \mathcal{D}_{KL}\left( q_\phi(z_{t+1} \mid \mathbf{x}_{1:t+1}, z_t) \,\|\, p_\vartheta(z_{t+1} \mid z_{1:t}) \right) \right]", False)
eq(r"- \mathcal{D}_{KL}\left( q_\phi(z_1 \mid \mathbf{x}_1) \,\|\, p_\vartheta(z_1) \right) + \gamma \sum_{t=1}^{w} \sum_{z_t=1}^{k} p_\vartheta(\boldsymbol{\mu}_{z_t}) \log p_\vartheta(\mathbf{x}_t \mid z_t)", False)
p("Ý nghĩa từng số hạng:", indent=False)
bullets([
    "**Số hạng 1 – tái tạo động:** các quan sát $\\mathbf{x}_t$ phải được giải thích tốt bởi cụm mà mạng suy diễn gán cho "
    "chúng; gradient kéo các tâm $\\boldsymbol{\\mu}_c$ về vùng dày đặc của các đặc trưng thuộc cụm $c$.",
    "**Số hạng 2 – KL chuyển trạng thái:** buộc phân phối chuyển của mô hình sinh $p_\\vartheta(z_{t+1} \\mid z_{1:t})$ – "
    "thứ duy nhất có sẵn khi dự báo tương lai – khớp với hậu nghiệm $q_\\phi$ (vốn được nhìn thấy dữ liệu). Đây là số hạng "
    "“dạy” RNN chuyển trạng thái dự đoán cụm kế tiếp.",
    "**Số hạng 3 – KL ban đầu:** $p_\\vartheta(z_1)$ là tiên nghiệm đều.",
    "**Số hạng 4 – hỗn hợp cơ sở:** điều chuẩn quan hệ giữa các thành phần cơ sở; tương đương log-likelihood của một "
    "GMM tĩnh (phân cụm toàn cục trên mọi $\\mathbf{x}_t$).",
])
p("Ba số hạng đầu mã hoá tiêu chí học cho phần *điều chỉnh động*; số hạng cuối (sau $\\gamma$) điều chuẩn các thành phần của "
  "hỗn hợp cơ sở. Tương tự VAE, cấu trúc này giúp chống quá khớp và cải thiện khả năng tổng quát. Mọi số hạng log-likelihood "
  "chỉ được tính trên **các giá trị quan sát được**, bằng cách nhân với mặt nạ $\\mathbf{m}_t$:")
eq(r"\log p_\vartheta(\mathbf{x}_t \mid z_t = c) = -\frac{1}{2} \sum_{i=1}^{d} m^i_t \left[ \sigma \, (x^i_t - \mu^i_c)^2 - \log \frac{\sigma}{2\pi} \right]")

h("3.6. Cơ chế cổng cho phân phối động", 2)
p("Trong (17), $\\gamma$ là siêu tham số cần dò trên tập validation. Để tránh công sức này, DGM² thay $\\gamma$ bằng một "
  "**hàm cổng** dùng thông tin trích xuất bởi mạng suy diễn (khối “0 1” màu cam ở Hình 2c):")
eq(r"\gamma(\tilde{\mathbf{h}}_t) = \mathrm{sigmoid}\left( \mathrm{MLP}(\tilde{\mathbf{h}}_t) \right)")
p("Khi đó $\\boldsymbol{\\psi}_t$ trở thành một phân phối **có cổng**, được điều chỉnh động tại mỗi bước: lúc mô hình "
  "tự tin về động học (ví dụ chuỗi đang ổn định trong một trạng thái), $\\gamma_t$ nhỏ và dự báo dựa chủ yếu vào "
  "$p(z_{t+1} \\mid z_{1:t})$; lúc không chắc chắn, $\\gamma_t$ lớn hơn và dự báo “lùi” về phân phối cơ sở toàn cục.")

h("3.7. Huấn luyện mô hình", 2)
p("Toàn bộ tham số $\\{\\boldsymbol{\\alpha}, \\boldsymbol{\\rho}, \\vartheta, \\phi\\}$ của lớp tiền nội suy, mạng sinh và mạng suy "
  "diễn được học đồng thời bằng cách cực đại ELBO (23) với gradient ngẫu nhiên (Adam). Các điểm kỹ thuật chính:")
bullets([
    "**Số hạng 1** tính giải tích được vì $z_t$ rời rạc, nhưng cần xác suất biên $q_\\phi(z_t \\mid \\mathbf{x}_{1:t})$ – không phải "
    "đầu ra trực tiếp của mạng suy diễn. Nó được tính đệ quy từ các xác suất có điều kiện: "
    "$q_\\phi(z_t = c \\mid \\mathbf{x}_{1:t}) = \\sum_{c'} q_\\phi(z_t = c \\mid \\mathbf{x}_{1:t}, z_{t-1} = c') \\, q_\\phi(z_{t-1} = c' \\mid \\mathbf{x}_{1:t-1})$.",
    "**Số hạng 2** được tính tuần tự nên dùng **lấy mẫu tổ tiên** (ancestral sampling): rút $z_t$ từ bước 1 đến $w$ để xấp xỉ "
    "phân phối $q_\\phi$; bước lấy mẫu dùng **Gumbel-softmax** (mục 2.7) để khả vi.",
    "**Ước lượng mật độ của hỗn hợp cơ sở** $p(\\boldsymbol{\\mu})$: với $n$ vector $\\mathbf{x}_t$ trong batch (tập $\\mathcal{X}$), "
    "xác suất trộn được ước lượng bằng trung bình xác suất thành viên suy diễn được:",
])
eq(r"p(\boldsymbol{\mu}_c) = \frac{1}{n} \sum_{\mathbf{x}_t \in \mathcal{X}} q_\phi(z_t = c \mid \mathbf{x}_{1:t}, z_{t-1}), \qquad c = 1, \dots, k")
p("Cài đặt gốc của tác giả còn dùng thêm **KL annealing** (tham số --max_kl, --wait_epoch) và nhiệt độ Gumbel ủ dần "
  "(temp_init = 0,5, temp_min = 0,1).")

h("3.8. Dự báo", 2)
p("Khi dự báo, mạng suy diễn “đọc” $w$ bước quá khứ (đã tiền nội suy) để có hậu nghiệm về cụm và trạng thái của RNN "
  "chuyển trạng thái. Sau đó mô hình sinh được **cuộn tiếp** (roll-out) $r$ bước mà không cần dữ liệu: tại mỗi bước tính "
  "$p(z_{t+1} \\mid z_{1:t})$, cổng $\\gamma_{t+1}$, hỗn hợp động $\\boldsymbol{\\psi}_{t+1}$, và giá trị dự báo là **kỳ vọng** của "
  "hỗn hợp Gaussian:")
eq(r"\tilde{\mathbf{x}}_{t+1} = \mathbb{E}\left[\mathbf{x}_{t+1} \mid z_{1:t}\right] = \sum_{c=1}^{k} \psi_{t+1}[c] \, \boldsymbol{\mu}_c")
p("Vì là tổ hợp lồi của các tâm cụm, dự báo luôn nằm trong “vùng dữ liệu hợp lý” đã học từ toàn bộ tập huấn luyện – "
  "một dạng điều chuẩn mạnh giúp chống nhiễu khi quá khứ rất thưa. Ngoài ra, giá trị sinh ra tại các vị trí bị thiếu trong "
  "quá khứ có thể dùng như **một lần nội suy mới**, tốt hơn tiền nội suy (Bảng 4 ở Chương 4).")

h("3.9. So sánh DGM² với GMM-HMM", 2)
table(["Khía cạnh", "GMM-HMM (cổ điển)", "DGM² (GMM + DNN)"], [
    ["Biến ẩn", "Trạng thái rời rạc $s_t$", "Biến cụm rời rạc $z_t$"],
    ["Chuyển trạng thái", "Ma trận $A$, Markov bậc 1: $p(s_{t+1}|s_t)$", "RNN/LSTM/ODE-RNN: $p(z_{t+1}|z_{1:t})$, nhớ toàn bộ lịch sử"],
    ["Phát xạ", "Gaussian riêng cho từng trạng thái", "Hỗn hợp Gaussian động $\\boldsymbol{\\psi}_t$ = điều chỉnh động + hỗn hợp cơ sở"],
    ["Suy diễn", "Chính xác: forward–backward $O(Tk^2)$", "Xấp xỉ biến phân: mạng suy diễn có cấu trúc, quy nạp"],
    ["Huấn luyện", "EM (Baum–Welch)", "SGD trên ELBO, Gumbel-softmax, end-to-end"],
    ["Dữ liệu thiếu", "Phải nội suy trước", "Mặt nạ + lớp tiền nội suy học được"],
    ["Dự báo xa", "$\\boldsymbol{\\pi}_w A^h$ hội tụ nhanh về phân phối dừng", "Động học phi tuyến, có cổng $\\gamma_t$"],
], "So sánh hai cách kết hợp GMM với mô hình chuỗi thời gian.", col_widths=[3.2, 6.0, 6.8], font_size=10.5)
p("Có thể thấy DGM² là một sự tổng quát hoá của HMM Gaussian: nếu thay RNN bằng ma trận chuyển, đặt $\\gamma = 0$ và dùng "
  "hậu nghiệm chính xác thì ta thu lại gần đúng một HMM. Ngược lại, nếu đặt $\\gamma = 1$ thì bỏ hẳn động học và thu được "
  "một GMM tĩnh – đây chính là hai trường hợp biên trong phân tích ablation của bài báo.")

# =============================================================== CHƯƠNG 4
h("Chương 4. Kết quả thực nghiệm trong bài báo")
h("4.1. Dữ liệu và thiết lập", 2)
table(["Bộ dữ liệu", "Mô tả", "Tỉ lệ thiếu", "Nhiệm vụ"], [
    ["USHCN", "Khí tượng hằng ngày, 5 biến (nhiệt độ TB, lượng mưa…), 5000 đoạn 100 ngày của các trạm bang NY, 1900–2000", "10,4%", "80 ngày → 20 ngày"],
    ["KDD-CUP", "PM2.5 theo giờ của 35 trạm quan trắc ở Bắc Kinh, 01–12/2017", "16,5%", "24 giờ → 12 giờ"],
    ["MIMIC-III", "31.332 lượt nằm ICU của người lớn, 17 chỉ số lâm sàng trong 72 giờ đầu", "72,7%", "48 giờ → 24 giờ"],
], "Ba bộ dữ liệu thực được dùng trong bài báo.", col_widths=[2.4, 8.2, 2.1, 3.3], font_size=10.5)
p("Các phương pháp so sánh: VAR, LSTM, DMM, XGBoost (không xử lý thiếu – nối thêm mặt nạ vào đầu vào), GRU-I (nội suy "
  "bằng GAN rồi dự báo), GRU-D, IPN, LGNet (nội suy tham số hoá và RNN huấn luyện đồng thời) và Latent-ODE. Dữ liệu được "
  "chia 70/10/20 cho train/valid/test; mọi mô hình dùng Adam, siêu tham số chọn trên tập validation. Với DGM², số cụm "
  "$k$ được dò từ 10 đến 200, $\\gamma$ và $\\sigma$ trong $\\{10^{-5}, \\dots, 10^{-1}\\}$, kích thước ẩn trong "
  "$\\{10, \\dots, 50\\}$. Thước đo: RMSE và MAE (càng nhỏ càng tốt), trung bình 5 lần chạy.")
h("4.2. Kết quả dự báo", 2)
T1 = [["VAR", "6.7154", "3.7420", "0.9811", "0.7927", "0.8164", "0.5052"],
      ["LSTM", "1.0587", "0.8203", "0.6340", "0.4456", "0.7465", "0.5082"],
      ["DMM", "0.9852", "0.7510", "0.6068", "0.4058", "0.7067", "0.5052"],
      ["XGBoost", "0.9900", "0.7209", "0.8664", "0.7816", "0.8841", "0.7580"],
      ["GRU-I", "1.0322", "0.8256", "0.9491", "0.7764", "0.8233", "0.5925"],
      ["GRU-D", "1.0495", "0.8502", "0.9695", "0.7912", "0.7268", "0.5051"],
      ["IPN", "0.9888", "0.7856", "0.6097", "0.4204", "0.7207", "0.4834"],
      ["LGNet", "0.9590", "0.7093", "0.5883", "0.3841", "0.7346", "0.5181"],
      ["L-ODE", "0.9315", "0.7325", "0.6171", "0.4216", "0.8226", "0.5834"],
      ["DGM²-L", "0.9143", "0.7089", "0.5426", "0.3848", "0.6975", "0.4748"],
      ["DGM²-O", "0.9003", "0.6876", "0.4983", "0.3367", "0.6835", "0.4646"]]
table(["Phương pháp", "MIMIC RMSE", "MIMIC MAE", "USHCN RMSE", "USHCN MAE", "KDD RMSE", "KDD MAE"], T1,
      "Kết quả dự báo (Bảng 1 trong bài báo, bỏ phần độ lệch chuẩn). In đậm: tốt nhất.",
      col_widths=[2.6, 2.2, 2.2, 2.2, 2.2, 2.2, 2.2], bold_best={(10, j) for j in range(1, 7)}, font_size=10)
p("Nhận xét của tác giả: (1) các phương pháp theo khuôn khổ nội suy – dự báo đồng thời (IPN, LGNet) thường tốt hơn các "
  "phương pháp truyền thống, khẳng định lợi ích của việc học mẫu hình thiếu theo nhiệm vụ; (2) DMM cho kết quả tốt dù không "
  "có thiết kế đặc biệt cho dữ liệu thưa, cho thấy ưu thế của mô hình sinh trong dự báo; (3) DGM²-L tốt hơn các phương "
  "pháp khác trong đa số trường hợp, chứng tỏ hiệu quả của việc mô hình hoá động cấu trúc cụm tiềm ẩn; (4) DGM²-O kết "
  "hợp thêm ưu điểm của ODE và cải thiện RMSE tương đối ít nhất 3,5%, 18,1% và 3,4% trên MIMIC-III, USHCN và KDD-CUP.")
h("4.3. Chất lượng nội suy và ablation", 2)
table(["Thiết lập", "MIMIC-III", "USHCN", "KDD-CUP"], [
    ["DGM²-L – trước (tiền nội suy)", "1.4111", "0.7780", "5.2363"],
    ["DGM²-L – sau (khối dự báo)", "**0.9052**", "**0.5250**", "**0.5506**"],
    ["DGM²-O – trước (tiền nội suy)", "1.4186", "0.4761", "4.2868"],
    ["DGM²-O – sau (khối dự báo)", "**0.8979**", "**0.4663**", "**0.5362**"],
], "RMSE nội suy trước/sau khối dự báo khi xoá ngẫu nhiên 10% quan sát (Bảng 2 trong bài báo).",
      col_widths=[6.4, 3.2, 3.2, 3.2], font_size=10.5)
p("Giá trị sinh ra bởi khối dự báo tại các ô bị xoá chính xác hơn hẳn giá trị của lớp tiền nội suy, chứng tỏ cấu trúc "
  "cụm học được giúp sinh ra chuỗi gần với thực tế.")
table(["Mô hình", "MIMIC-III", "USHCN", "KDD-CUP"], [
    ["(a) $\\gamma = 1$ (chỉ hỗn hợp cơ sở, không động)", "0.9832", "0.9913", "0.9998"],
    ["(b) $\\gamma = 0$ (không có hỗn hợp cơ sở)", "0.9191", "0.5151", "0.7533"],
    ["(c) $\\gamma = 10^{-2}$", "0.9033", "**0.4958**", "0.6878"],
    ["(d) Cổng $\\gamma(\\cdot)$", "**0.9003**", "0.4983", "**0.6835**"],
], "Phân tích ablation của $\\gamma$, RMSE (Bảng 3 trong bài báo).", col_widths=[7.0, 3.0, 3.0, 3.0], font_size=10.5)
p("Hai trường hợp biên đều kém, đặc biệt khi bỏ động học ($\\gamma = 1$, tương đương GMM tĩnh). $\\gamma = 10^{-2}$ là lựa "
  "chọn tối ưu từ grid search, cho thấy chỉ cần một lượng nhỏ hỗn hợp cơ sở; hàm cổng cho kết quả tương đương mà không "
  "cần dò siêu tham số.")
h("4.4. Độ bền theo tỉ lệ thiếu và trực quan hoá", 2)
fig(os.path.join(FIG, "fig3_robustness.png"),
    "RMSE theo tỉ lệ quan sát bị xoá thêm trên USHCN và KDD-CUP (Hình 3 trong bài báo).", 13)
p("Khi xoá ngẫu nhiên thêm tỉ lệ $\\delta$ từ 0 đến 0,8 các giá trị quan sát, sai số của các phương pháp không xử lý thiếu "
  "(VAR, LSTM, DMM) tăng nhanh; GRU-D, LGNet, L-ODE ổn định hơn nhưng vẫn giảm chất lượng khi $\\delta \\ge 0{,}6$. Trong "
  "khi đó DGM²-L và DGM²-O gần như không đổi và luôn tốt nhất – nhờ mô hình hoá cấu trúc cụm bền vững.")
fig(os.path.join(FIG, "fig4_tsne.png"),
    "t-SNE của các đặc trưng thời gian (chấm tròn, độ trong suốt khác nhau = các MTS khác nhau) và các tâm Gaussian học "
    "được (dấu +) trên MIMIC-III và USHCN (Hình 4 trong bài báo).", 16)
p("Các cụm hiện rõ; các đặc trưng từ những MTS khác nhau có thể nằm cùng một cụm – nghĩa là các bệnh nhân khác nhau có "
  "thể chia sẻ cùng một trạng thái bệnh lý ở những giai đoạn khác nhau. Các tâm học được nằm ở vùng dày đặc của tập huấn "
  "luyện và cũng khớp với dữ liệu kiểm thử, giải thích vì sao chuỗi mới được dự báo tốt.")

# =============================================================== CHƯƠNG 5
h("Chương 5. Demo ứng dụng: dự báo khí hậu trên dữ liệu thưa USHCN")
h("5.1. Bài toán và dữ liệu", 2)
p("Demo tái hiện thí nghiệm USHCN của bài báo: mỗi mẫu là một MTS 100 ngày với 5 biến khí hậu của mạng lưới trạm khí "
  "tượng lịch sử Hoa Kỳ (USHCN) – lượng mưa, lượng tuyết rơi, độ dày tuyết, nhiệt độ cao nhất và thấp nhất. Dùng "
  "**80 ngày quá khứ** để dự báo **20 ngày tương lai**. Dữ liệu lấy trực tiếp từ thư mục dataset_dir của repo "
  "github.com/KnowledgeDiscovery/DynamicGaussianMixture (4000 mẫu train, 1000 mẫu test). Tiền xử lý giống repo gốc: "
  "loại ngoại lai ngoài khoảng trung bình ± 3 độ lệch chuẩn (coi như thiếu) và chuẩn hoá z-score từng biến theo thống kê "
  "của các giá trị quan sát được trong tập train; 12,5% tập train được tách làm validation. Tỉ lệ thiếu sau tiền xử lý "
  "khoảng 10,5%. Vì repo gốc không ghi rõ thứ tự cột, các biến được gọi chung là “Biến 1…5” trong demo.")
h("5.2. Cài đặt", 2)
p("DGM²-L được cài đặt lại gọn trong khoảng 200 dòng PyTorch (mã gốc của tác giả dài hàng nghìn dòng, viết cho Python "
  "3.7 và khó đọc). Cấu trúc thư mục demo:")
table(["Tệp", "Nội dung", "Công thức"], [
    ["data.py", "Nạp USHCN, loại ngoại lai, chuẩn hoá, tách train/valid/test, xoá thêm quan sát", "–"],
    ["dgm2.py – PreImputation", "Kernel Gaussian, hàm cường độ $\\lambda$, tương quan $\\rho$", "(12)–(14)"],
    ["dgm2.py – DGM2", "Mạng sinh LSTM, hỗn hợp động, mạng suy diễn, cổng, ELBO, dự báo", "(15)–(27)"],
    ["baselines.py", "Naive (lặp giá trị cuối), GMM-HMM (hmmlearn), LSTM encoder–decoder", "(5)–(7)"],
    ["train.py", "Huấn luyện, đánh giá; các thí nghiệm main / ablation / robustness", "–"],
    ["make_figures.py", "Vẽ các hình kết quả cho báo cáo", "–"],
    ["app.py", "Ứng dụng web tương tác Streamlit", "–"],
], "Cấu trúc mã nguồn demo và ánh xạ tới các công thức trong báo cáo.", col_widths=[4.2, 8.8, 3.0], font_size=10.5)
p("Đoạn mã cốt lõi của vòng lặp suy diễn – sinh (rút gọn từ dgm2.py):", indent=False)
R.code('''for t in range(T):
    p_t = uniform(k) if t == 0 else softmax(p_mlp(h_gen))  # p(z_t|z_1:t-1)  (16)
    logits = q_mlp(cat[h_enc[t], z_prev])                 # q(z_t|x_1:t,z_t-1) (22)
    q_t = softmax(logits)
    z_t = q_t   # hoặc gumbel_softmax(logits, tau)
    h_gen = gen_lstm(z_t, h_gen)                          # RNN chuyển trạng thái
    kl += KL(q_t || p_t)                                  # số hạng 2, 3 của ELBO
logpx[c] = -0.5 * sum_i m[i] * ((x[i] - mu[c,i])**2 / var + log(2*pi*var))
rec  = (1-g_t) * sum_c q_t[c]*logpx[c] + g_t * sum_c p_mu[c]*logpx[c]
loss = -rec / N_obs + beta * kl / N_steps''', size=9)
p("Một số lựa chọn cài đặt (đều bám theo mã gốc của tác giả hoặc là chi tiết bài báo không nêu):", indent=False)
bullets([
    "**Đầu vào của LSTM chuyển trạng thái** là vector xác suất $q_\\phi(z_t)$ (mềm) như mã gốc; tuỳ chọn soft_transition=False "
    "dùng mẫu Gumbel-softmax đúng như mô tả trong bài báo (kết quả gần tương đương, xem Bảng 7).",
    "**Chuẩn hoá hàm mất mát** như mã gốc: số hạng tái tạo chia cho số giá trị quan sát, KL chia cho số bước thời gian, "
    "hệ số KL $\\beta$ tăng tuyến tính trong 25% số epoch đầu (KL annealing).",
    "**Mẫu số của công thức (14)** dùng $\\sum_j |\\rho_{ij}| \\lambda_j$ để $\\hat{x}^i$ luôn là trung bình có trọng số (khi "
    "$\\boldsymbol{\\rho} = \\mathbf{I}$ thì $\\hat{x}^i = \\bar{x}^i$); $\\lambda$ của biến $j$ được tính với mặt nạ của chính biến $j$.",
    "**Khởi tạo tâm** $\\boldsymbol{\\mu}$ bằng các vector quan sát đầy đủ chọn ngẫu nhiên; $p(\\boldsymbol{\\mu})$ theo (26) được "
    "làm trơn bằng trung bình động lũy thừa qua các batch để dùng lại lúc dự báo.",
    "**Dự báo** theo (27); trong lúc cuộn, LSTM chuyển trạng thái nhận xác suất mềm $p(z_{t+1} \\mid z_{1:t})$ và RNN suy diễn "
    "nhận giá trị vừa dự báo (mặt nạ = 1) để cập nhật cổng $\\gamma$ – giống mã gốc.",
])
p("Các mô hình so sánh: **Naive** (lặp lại giá trị quan sát cuối), **GMM-HMM** (HMM Gaussian hiệp phương sai chéo, "
  "20 trạng thái, Baum–Welch 30 vòng, dự báo theo (7), dữ liệu thiếu điền bằng giá trị quan sát gần nhất) và **LSTM** "
  "encoder–decoder (đầu vào nối $[\\mathbf{x}_t \\odot \\mathbf{m}_t, \\mathbf{m}_t]$ như bài báo, huấn luyện trực tiếp bằng MSE "
  "trên 20 bước tương lai).")

# ---- kết quả demo
main, abl, rob = load("main"), load("ablation"), load("robustness")
cfg = json.load(open(os.path.join(RES, "config.json"), encoding="utf8")) if os.path.exists(os.path.join(RES, "config.json")) else {}
h("5.3. Kết quả", 2)
if cfg:
    p(f"Siêu tham số DGM²-L (chọn trên tập validation): $k = {cfg.get('k')}$ cụm, kích thước ẩn {cfg.get('hidden')}, "
      f"phương sai $\\sigma^{{-1}} = {cfg.get('var')}$, $\\beta_{{max}} = {cfg.get('max_kl')}$, Adam lr = {cfg.get('lr')}, "
      f"{cfg.get('epochs')} epoch, batch 128, dùng hàm cổng $\\gamma(\\tilde{{\\mathbf{{h}}}}_t)$. Toàn bộ huấn luyện chạy trên CPU.")
# ---- bảng grid search đọc từ log
import glob, re as _re
LOGS = os.path.join(HERE, "..", "demo", "logs")
sweep_rows = []
for f in sorted(glob.glob(os.path.join(LOGS, "sweep*.log"))):
    name = os.path.basename(f)[:-4].split("_", 1)[1]
    vals = [float(v) for v in _re.findall(r"val RMSE ([0-9.]+)", open(f, encoding="utf8").read())]
    if not vals:
        continue
    g = lambda pat, dflt: (_re.search(pat, name).group(1) if _re.search(pat, name) else dflt)
    sweep_rows.append([g(r"k_(\d+)", "30"), g(r"hidden_(\d+)", "40"), g(r"var_([\d.]+)", "0.1"),
                       g(r"max_kl_([\d.]+)", "1.0"), g(r"lr_([\de.-]+)", "3e-3"),
                       "Gumbel" if "soft_transition_False" in name else "mềm", str(len(vals)), f"{min(vals):.4f}"])
if sweep_rows:
    bestv = min(float(r_[-1]) for r_ in sweep_rows)
    table(["$k$", "Ẩn", r"$\sigma^{-1}$", r"$\beta_{max}$", "lr", "Chuyển tt.", "Epoch", "Val RMSE"], sweep_rows,
          "Dò siêu tham số DGM²-L trên tập validation (logs/sweep*.log).",
          col_widths=[1.4, 1.4, 1.6, 1.6, 1.6, 2.2, 1.6, 2.4], font_size=10,
          bold_best={(i, 7) for i, r_ in enumerate(sweep_rows) if float(r_[-1]) == bestv})
    p("Số cụm $k = 50$ tốt hơn rõ rệt so với $k = 100$ (hội tụ chậm hơn nhiều trong cùng số epoch) và $k = 40$; tốc độ học "
      "lớn hơn giúp hội tụ nhanh; dùng xác suất mềm hay mẫu Gumbel-softmax cho LSTM chuyển trạng thái cho kết quả gần như "
      "nhau. Một phát hiện quan trọng khi cài đặt: nếu trọng số KL quá lớn (ví dụ $\\beta = 5$ với chuẩn hoá của demo), "
      "hậu nghiệm $q_\\phi$ “sập” về tiên nghiệm (KL ≈ 0) và mô hình chỉ dự báo giá trị trung bình (RMSE ≈ 0,99).")

if main:
    best = min(main.values(), key=lambda v: v["RMSE"])["RMSE"]
    NAMES = {"Naive (last value)": "Naive (lặp giá trị cuối)", "GMM-HMM": "GMM-HMM (20 trạng thái)",
             "LSTM": "LSTM encoder–decoder", "DGM2-L (gate)": "DGM²-L (cổng γ)"}
    rows = [[NAMES.get(k, k), f"{v['RMSE']:.4f}", f"{v['MAE']:.4f}"] for k, v in main.items()]
    bb = {(i, 1) for i, (k, v) in enumerate(main.items()) if v["RMSE"] == best}
    bestmae = min(v["MAE"] for v in main.values())
    bb |= {(i, 2) for i, (k, v) in enumerate(main.items()) if v["MAE"] == bestmae}
    table(["Mô hình", "RMSE", "MAE"], rows, "Kết quả dự báo 20 ngày trên 1000 mẫu test USHCN của demo (không gian chuẩn hoá).",
          col_widths=[6.0, 3.0, 3.0], bold_best=bb)
    p("[[NHAN_XET_MAIN]]")
if os.path.exists(os.path.join(RES, "forecast_example_123.png")):
    fig(os.path.join(RES, "forecast_example_123.png"),
        "Ví dụ dự báo trên mẫu test số 123: chấm đen là quan sát thực, nét đứt cam là giá trị tiền nội suy ở quá khứ, vùng xám "
        "là 20 ngày cần dự báo.", 15.5)
if os.path.exists(os.path.join(RES, "clusters_example_123.png")):
    fig(os.path.join(RES, "clusters_example_123.png"),
        "Cấu trúc cụm tiềm ẩn của cùng mẫu: trên – xác suất thuộc cụm theo thời gian (trái vạch xanh: hậu nghiệm "
        "$q_\\phi$ ở quá khứ; phải vạch: hỗn hợp động $\\boldsymbol{\\psi}_t$ dùng để dự báo); dưới – giá trị cổng "
        "$\\gamma(\\tilde{\\mathbf{h}}_t)$.", 15.5)
if os.path.exists(os.path.join(RES, "tsne_clusters.png")):
    fig(os.path.join(RES, "tsne_clusters.png"),
        "t-SNE các vector đặc trưng $\\mathbf{x}_t$ (chấm xanh, mỗi độ đậm là một MTS) và các tâm Gaussian $\\boldsymbol{\\mu}_c$ "
        "học được (dấu + cam) – tái hiện Hình 4(c)(d) của bài báo bằng mô hình của demo.", 15.5)
    p("[[NHAN_XET_CLUSTER]]")
if abl:
    rows = [[k, f"{v['RMSE']:.4f}", f"{v['MAE']:.4f}"] for k, v in abl.items()]
    table(["Biến thể", "RMSE", "MAE"], rows, "Ablation của $\\gamma$ trong demo (USHCN, tập test).", col_widths=[7.5, 3.0, 3.0])
    p("[[NHAN_XET_ABL]]")
if rob:
    ratios = list(rob)
    models_ = list(rob[ratios[0]])
    rows = [[m_] + [f"{rob[r_][m_]['RMSE']:.4f}" for r_ in ratios] for m_ in models_]
    table(["Mô hình"] + [f"δ = {float(r_):.1f}" for r_ in ratios], rows,
          "RMSE khi xoá thêm tỉ lệ $\\delta$ quan sát ở 80 ngày quá khứ (cả train và test).",
          col_widths=[4.5] + [2.3] * len(ratios), font_size=10.5)
    if os.path.exists(os.path.join(RES, "robustness.png")):
        fig(os.path.join(RES, "robustness.png"), "Độ bền của các mô hình theo tỉ lệ quan sát bị xoá thêm (demo).", 15)
    p("[[NHAN_XET_ROB]]")
if os.path.exists(os.path.join(RES, "training_curve.png")):
    fig(os.path.join(RES, "training_curve.png"), "Đường cong huấn luyện DGM²-L: số hạng tái tạo, KL và RMSE validation.", 15.5)

h("5.4. Ứng dụng web tương tác", 2)
p("Ứng dụng Streamlit (app.py) cho phép người dùng khám phá mô hình trực quan, gồm 4 tab:")
bullets([
    "**Dự báo:** chọn một mẫu test, tuỳ chọn xoá thêm một tỉ lệ quan sát ở 80 ngày quá khứ (thanh trượt 0–90%), xem giá "
    "trị tiền nội suy, dự báo 20 ngày của DGM²-L, GMM-HMM, LSTM, Naive so với thực tế, cùng RMSE/MAE của riêng mẫu đó.",
    "**Cụm tiềm ẩn & cổng γ:** bản đồ nhiệt xác suất cụm theo thời gian (hậu nghiệm ở quá khứ, $\\boldsymbol{\\psi}_t$ ở tương "
    "lai), chuỗi cụm có xác suất lớn nhất, đồ thị $\\gamma_t$ và phân phối hỗn hợp cơ sở $p(\\boldsymbol{\\mu})$.",
    "**Không gian cụm:** chiếu PCA các vector đặc trưng tô màu theo cụm cùng các tâm $\\boldsymbol{\\mu}_c$.",
    "**Kết quả thực nghiệm:** các bảng và hình của mục 5.3.",
])
h("5.5. Hướng dẫn chạy", 2)
R.code('''cd demo
pip install torch numpy matplotlib scikit-learn hmmlearn streamlit
python train.py --exp main --epochs 40   # huấn luyện (CPU, ~10-15 phút)
python make_figures.py                    # vẽ hình vào demo/results/
streamlit run app.py                      # mở http://localhost:8501''')
p("Các thí nghiệm ablation (--exp ablation) và độ bền (--exp robustness) đã được cài đặt sẵn trong train.py nhưng khá nặng "
  "trên CPU (huấn luyện lại 5–15 mô hình), nên chưa được chạy trong báo cáo này. Các checkpoint đã huấn luyện sẵn nằm trong demo/checkpoints/, nên có thể chạy ngay streamlit run app.py mà không cần "
  "huấn luyện lại.")

# =============================================================== CHƯƠNG 6
h("Chương 6. Kết luận")
p("Báo cáo đã trình bày cơ sở lý thuyết của việc mô hình hoá chuỗi thời gian nhiều chiều bằng hỗn hợp Gaussian kết hợp "
  "với mô hình chuỗi thời gian, từ GMM – EM, HMM Gaussian đến mô hình hiện đại DGM². Ý tưởng cốt lõi của DGM² là **mô "
  "hình hoá sự chuyển dịch của các cụm tiềm ẩn được chia sẻ** thay vì các đặc trưng thưa riêng lẻ, và **phát xạ từ một hỗn "
  "hợp Gaussian động** – tổ hợp giữa dự đoán động của RNN và một hỗn hợp cơ sở toàn cục, được điều tiết bởi một hàm cổng. "
  "Nhờ khuôn khổ suy diễn biến phân với mạng suy diễn có cấu trúc, Gumbel-softmax và lớp tiền nội suy học được, mô hình "
  "huấn luyện end-to-end và suy diễn quy nạp cho chuỗi mới.")
p("[[KET_LUAN_DEMO]]")
p("**Hướng phát triển:** (1) dùng Gaussian có hiệp phương sai học được hoặc phương sai riêng từng cụm để mô hình hoá độ "
  "bất định tốt hơn và đưa ra khoảng dự báo; (2) thay LSTM bằng ODE-RNN (DGM²-O) hoặc Transformer; (3) áp dụng hỗn hợp "
  "Gaussian động cho các dữ liệu tuần tự khác như văn bản, đồ thị động, video (như tác giả đề xuất); (4) kết hợp thêm "
  "mục tiêu dự báo trực tiếp nhiều bước vào ELBO để cải thiện dự báo xa.")

# =============================================================== TÀI LIỆU
h("Tài liệu tham khảo")
refs = [
    "Wu, Y.; Ni, J.; Cheng, W.; Zong, B.; Song, D.; Chen, Z.; Liu, Y.; Zhang, X.; Chen, H.; Davidson, S. B. (2021). Dynamic "
    "Gaussian Mixture based Deep Generative Model for Robust Forecasting on Sparse Multivariate Time Series. AAAI 35(1): 651–659. "
    "https://ojs.aaai.org/index.php/AAAI/article/view/16145",
    "Mã nguồn DGM²: https://github.com/KnowledgeDiscovery/DynamicGaussianMixture",
    "Krishnan, R. G.; Shalit, U.; Sontag, D. (2017). Structured Inference Networks for Nonlinear State Space Models. AAAI.",
    "Che, Z.; Purushotham, S.; Cho, K.; Sontag, D.; Liu, Y. (2018). Recurrent Neural Networks for Multivariate Time Series with Missing Values. Scientific Reports 8(1).",
    "Shukla, S. N.; Marlin, B. (2019). Interpolation-Prediction Networks for Irregularly Sampled Time Series. ICLR.",
    "Rubanova, Y.; Chen, R. T.; Duvenaud, D. (2019). Latent ODEs for Irregularly-Sampled Time Series. NeurIPS.",
    "Tang, X. et al. (2020). Joint Modeling of Local and Global Temporal Dynamics for Multivariate Time Series Forecasting with Missing Values. AAAI.",
    "Jang, E.; Gu, S.; Poole, B. (2017). Categorical Reparameterization with Gumbel-Softmax. ICLR.",
    "Kingma, D. P.; Welling, M. (2013). Auto-Encoding Variational Bayes. arXiv:1312.6114.",
    "Hoffman, M. D.; Blei, D. M.; Wang, C.; Paisley, J. (2013). Stochastic Variational Inference. JMLR 14(1).",
    "Rabiner, L. R. (1989). A Tutorial on Hidden Markov Models and Selected Applications in Speech Recognition. Proc. IEEE 77(2).",
    "Bishop, C. M. (2006). Pattern Recognition and Machine Learning, Chương 9 (Mixture Models and EM) và 13 (Sequential Data). Springer.",
    "Hochreiter, S.; Schmidhuber, J. (1997). Long Short-Term Memory. Neural Computation 9(8).",
    "Maaten, L. v. d.; Hinton, G. (2008). Visualizing Data using t-SNE. JMLR 9.",
]
for i, r_ in enumerate(refs, 1):
    par = R.doc.add_paragraph(); par.paragraph_format.left_indent = Cm(0.8); par.paragraph_format.first_line_indent = Cm(-0.8)
    par.add_run(f"[{i}] {r_}").font.size = Pt(12)

# ---- thay các nhận xét (điền sau khi có số liệu)
NOTES = json.load(open(os.path.join(HERE, "notes.json"), encoding="utf8")) if os.path.exists(os.path.join(HERE, "notes.json")) else {}
for par in R.doc.paragraphs:
    for key in ["NHAN_XET_MAIN", "NHAN_XET_CLUSTER", "NHAN_XET_ABL", "NHAN_XET_ROB", "KET_LUAN_DEMO"]:
        if f"[[{key}]]" in par.text:
            for r_ in par.runs:
                r_.text = ""
            R._add_rich(par, NOTES.get(key, ""))
            if not NOTES.get(key):
                par._p.getparent().remove(par._p)

out = os.path.join(HERE, "BaoCao_DGM2_v2.docx")
R.save(out)
print("saved", out, "| equations:", R.eq_no, "figures:", R.fig_no, "tables:", R.tab_no)
