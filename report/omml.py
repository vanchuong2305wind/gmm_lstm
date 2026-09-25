"""Chuyển công thức LaTeX -> OMML (công thức native của Word) qua MathML + MML2OMML.XSL của Office."""
import copy, re
from lxml import etree
from latex2mathml.converter import convert

XSL = r"C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL"
_xslt = etree.XSLT(etree.parse(XSL))
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"

# latex2mathml bỏ mất các lệnh khoảng trắng -> thay bằng ký tự khoảng trắng Unicode trong \text{}
_SPACES = [(r"\qquad", "\u2003\u2003"), (r"\quad", "\u2003"), (r"\;", "\u2005"), (r"\,", "\u2009")]


def _prep(latex):
    latex = latex.replace(r"\arg\max", r"\mathrm{argmax}")
    latex = re.sub(r"\\log(?![a-zA-Z])", lambda _: r"\log\,", latex)
    for cmd, sp in _SPACES:
        latex = latex.replace(cmd, r"\text{" + sp + "}")
    return latex


def _fix_nary(root):
    """MML2OMML tạo <m:nary> với thân <m:e> rỗng rồi đặt biểu thức phía sau -> khoảng trống lớn.
    Chuyển phần tử ngay sau vào thân của toán tử tổng/tích."""
    for nary in reversed(list(root.iter(f"{{{M}}}nary"))):
        e = nary.find(f"{{{M}}}e")
        if e is None or len(e):
            continue
        nxt = nary.getnext()
        if nxt is not None:
            e.append(nxt)


def latex_to_omml(latex):
    tree = etree.fromstring(convert(_prep(latex)))
    root = _xslt(tree).getroot()          # <m:oMath>
    _fix_nary(root)
    return root


def add_equation(paragraph, latex):
    paragraph._p.append(copy.deepcopy(latex_to_omml(latex)))
    return paragraph
