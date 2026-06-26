#!/usr/bin/env python3
"""slothreport: markdown -> PDF(图文公式齐全)。
用法:  python3 md2pdf.py <report.md> [out.pdf]
做对了三件易错的事:
  1) 渲染前先「保护」$...$/$$...$$ 数学,避免 markdown 把 _ * 当强调符破坏公式;
  2) 图片转 base64 内嵌(不依赖相对路径/中文目录名,viewer 一定加载得到);
  3) 用 @font-face 显式喂一个单文件 CJK 字体 —— 否则无头 Chrome 读不到系统字体,
     正文中英文会全部空白(只有 SVG 公式和图能显示)。这是最坑的一步。
公式用 MathJax(SVG)渲染;最后用无头 Chrome 打印 PDF。无需 TeX Live。
"""
import re, sys, base64, pathlib, shutil, subprocess, markdown

SRC = pathlib.Path(sys.argv[1]).resolve()
OUT = pathlib.Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else SRC.with_suffix(".pdf")
root = SRC.parent
text = SRC.read_text(encoding="utf-8")

# --- 1) 保护数学,免被 markdown 破坏 ---
store = {}
def stash(m, tag):
    k = f"\x00{tag}{len(store)}\x00"; store[k] = m.group(0); return k
text = re.sub(r"\$\$.+?\$\$", lambda m: stash(m, "D"), text, flags=re.S)
text = re.sub(r"\$[^\$\n]+?\$", lambda m: stash(m, "I"), text)

# --- 2) markdown -> html,再还原数学 ---
body = markdown.markdown(text, extensions=["tables", "fenced_code", "attr_list", "sane_lists"])
for k, v in store.items():
    body = body.replace(k, v)

# --- 3) 图片 base64 内嵌 + <figure>/<figcaption> ---
def img_repl(m):
    alt, src = m.group("alt"), m.group("src")
    p = (root / src)
    if not p.exists(): return m.group(0)
    b64 = base64.b64encode(p.read_bytes()).decode()
    ext = p.suffix.lstrip(".").lower() or "png"
    cap = f"<figcaption>{alt}</figcaption>" if alt.strip() else ""
    return f'<figure><img src="data:image/{ext};base64,{b64}"/>{cap}</figure>'
body = re.sub(r'<img alt="(?P<alt>[^"]*)" src="(?P<src>[^"]+)"\s*/?>', img_repl, body)
body = re.sub(r"<p>(<figure>.*?</figure>)</p>", r"\1", body, flags=re.S)

# --- 4) 找单文件 CJK 字体(无头浏览器必需) ---
finder = pathlib.Path(__file__).parent / "find_cjk_font.sh"
font = ""
try:
    font = subprocess.run(["bash", str(finder)], capture_output=True, text=True).stdout.strip()
except Exception:
    pass
font_face = f"@font-face{{font-family:'CJK';src:url('file://{font}');}}" if font else ""
fam = "'CJK', sans-serif" if font else "sans-serif"
if not font:
    sys.stderr.write("WARN: 未找到单文件 CJK 字体,中文可能空白。装 Noto Sans CJK 或见 visuals_and_tools.md\n")

html = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<script>window.MathJax={{tex:{{inlineMath:[['$','$']],displayMath:[['$$','$$']]}},svg:{{fontCache:'global'}}}};</script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
<style>
{font_face}
@page {{ size: A4; margin: 16mm 14mm; }}
body, th, td, p, li, h1, h2, h3, figcaption, blockquote {{ font-family: {fam}; }}
body {{ font-size:10.5pt; line-height:1.62; color:#1a1a1a; }}
h1 {{ font-size:19pt; border-bottom:3px solid #fe2c55; padding-bottom:6px; margin:22px 0 14px; }}
h1:first-of-type {{ color:#fe2c55; }}
h2 {{ font-size:15pt; border-bottom:1px solid #ddd; padding-bottom:4px; margin:20px 0 10px; }}
h3 {{ font-size:12.5pt; margin:14px 0 6px; color:#333; }}
p {{ margin:7px 0; }}
blockquote {{ border-left:4px solid #fe2c55; background:#fff5f7; margin:10px 0; padding:7px 14px; color:#444; border-radius:0 4px 4px 0; }}
code {{ background:#f4f4f6; padding:1px 5px; border-radius:3px; font-family:"SF Mono",Menlo,{fam}; font-size:9pt; }}
pre {{ background:#f7f7f9; padding:10px 12px; border-radius:6px; overflow:auto; border:1px solid #eee; }}
pre code {{ background:none; padding:0; }}
table {{ border-collapse:collapse; width:100%; margin:12px 0; font-size:9.3pt; }}
th,td {{ border:1px solid #d0d0d7; padding:5px 9px; text-align:left; vertical-align:top; }}
th {{ background:#f0f0f4; font-weight:600; }}
tr:nth-child(even) td {{ background:#fafafb; }}
figure {{ margin:14px 0; text-align:center; page-break-inside:avoid; }}
figure img {{ max-width:96%; height:auto; border:1px solid #eee; border-radius:6px; }}
figcaption {{ font-size:8.6pt; color:#666; margin-top:5px; line-height:1.45; padding:0 6%; }}
mjx-container {{ overflow-x:auto; overflow-y:hidden; max-width:100%; }}
hr {{ border:none; border-top:1px solid #e2e2e2; margin:18px 0; }}
ul,ol {{ margin:6px 0; padding-left:24px; }} li {{ margin:3px 0; }}
strong {{ color:#0a0a0a; }}
</style></head><body>
{body}
</body></html>"""

html_path = OUT.with_suffix(".html")
html_path.write_text(html, encoding="utf-8")

# --- 5) 找浏览器,无头打印 PDF(用经典 --headless;--headless=new 在 mac 上常丢字体) ---
candidates = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    shutil.which("google-chrome"), shutil.which("chromium"), shutil.which("chromium-browser"),
]
chrome = next((c for c in candidates if c and pathlib.Path(c).exists()), None)
if not chrome:
    sys.stderr.write(f"WARN: 未找到 Chrome/Chromium。已生成 HTML: {html_path}\n请装浏览器,或自行把该 HTML 打印成 PDF。\n")
    sys.exit(2)

subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                "--virtual-time-budget=30000", f"--print-to-pdf={OUT}", f"file://{html_path}"],
               capture_output=True)
print(f"PDF: {OUT}  ({OUT.stat().st_size//1024} KB, images inlined: {body.count('data:image')}, font: {font or 'NONE'})")
