#!/usr/bin/env python3
"""slothreport: markdown -> PDF(图文公式齐全)。
用法:  python3 md2pdf.py <report.md> [out.pdf]
做对了四件易错的事:
  1) 渲染前先「保护」$...$/$$...$$ 数学,避免 markdown 把 _ * 当强调符破坏公式;
  2) 图片转 base64 内嵌(不依赖相对路径/中文目录名,viewer 一定加载得到);
  3) 用 @font-face 显式喂一个单文件 CJK 字体 —— 否则 mac/Linux 的无头 Chrome 读不到系统字体,
     正文中英文会全部空白(只有 SVG 公式和图能显示)。这是最坑的一步;
  4) headless 模式分平台:Chrome 132+ 删了经典 --headless,传它会静默不出 PDF,
     故非 mac 一律 --headless=new;mac 保留经典模式(新模式在 mac 上丢字体)。
公式用 MathJax(SVG)渲染;最后用无头 Chrome 打印 PDF。无需 TeX Live。
mac / Linux / Windows 都能跑:浏览器路径、file:// URI、headless 模式各平台分别处理,
Windows 上还接受 Edge(同为 Chromium),且找不到 CJK 字体也不影响中文(系统字体回退)。
退出码:2=没找到浏览器 3=浏览器没产出 PDF 4=目标 PDF 被阅读器占用。
"""
import re, os, sys, base64, pathlib, shutil, subprocess, tempfile, html as _html, markdown

IS_MAC = sys.platform == "darwin"
IS_WIN = os.name == "nt"

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
# 关键:还原时把 < > & 转义成 HTML 实体,否则公式里的 o_{i,<t}、\hat A<0 的 '<'
# 会被浏览器当成 HTML 标签起始而吞掉,打断 $$ 配对、整条公式渲染失败。
# 浏览器会把实体解码回 < 给 MathJax,故不影响数学。
body = markdown.markdown(text, extensions=["tables", "fenced_code", "attr_list", "sane_lists"])
for k, v in store.items():
    body = body.replace(k, _html.escape(v, quote=False))

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

# --- 4) 找单文件 CJK 字体(mac/Linux 的无头浏览器必需) ---
# Windows 例外:那里的 Chrome 会走系统字体回退,中文照样渲染,找不到只是少一层保险。
WIN_CJK = ("Deng.ttf", "simhei.ttf", "simkai.ttf", "simfang.ttf", "STSONG.TTF",
           "NotoSansSC-Regular.otf", "NotoSansCJKsc-Regular.otf")

def find_cjk_font():
    if IS_WIN:
        # .ttc 字体集合在 @font-face 下常加载失败,故只挑单文件 ttf/otf。
        dirs = [pathlib.Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"]
        if os.environ.get("LOCALAPPDATA"):  # 用户自装的字体在这里
            dirs.append(pathlib.Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Windows" / "Fonts")
        for d in dirs:
            for name in WIN_CJK:
                if (d / name).exists():
                    return str(d / name)
        return ""
    finder = pathlib.Path(__file__).parent / "find_cjk_font.sh"
    try:
        return subprocess.run(["bash", str(finder)], capture_output=True, text=True).stdout.strip()
    except Exception:
        return ""

font = find_cjk_font()
# 用 as_uri():Windows 路径带盘符和反斜杠,手拼 "file://" + path 得到的是坏 URI。
font_face = f"@font-face{{font-family:'CJK';src:url('{pathlib.Path(font).as_uri()}');}}" if font else ""
fam = "'CJK', sans-serif" if font else "sans-serif"
if not font:
    if IS_WIN:
        sys.stderr.write("NOTE: 未找到单文件 CJK 字体,交给 Chrome 的系统字体回退(Windows 上中文正常显示)。\n")
    else:
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

# --- 5) 找浏览器,无头打印 PDF ---
def find_browser():
    cands = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    # Windows:用环境变量拼,别硬编码盘符;Chrome/Edge 可能在 Program Files 也可能在用户目录。
    for var in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432", "LOCALAPPDATA"):
        base = os.environ.get(var)
        if not base:
            continue
        b = pathlib.Path(base)
        cands += [str(b / "Google" / "Chrome" / "Application" / "chrome.exe"),
                  str(b / "Microsoft" / "Edge" / "Application" / "msedge.exe"),
                  str(b / "Chromium" / "Application" / "chrome.exe")]
    cands += [shutil.which(n) for n in
              ("google-chrome", "chromium", "chromium-browser", "chrome", "msedge")]
    return next((c for c in cands if c and pathlib.Path(c).exists()), None)

chrome = find_browser()
if not chrome:
    sys.stderr.write(f"WARN: 未找到 Chrome/Chromium/Edge。已生成 HTML: {html_path}\n请装浏览器,或自行把该 HTML 打印成 PDF。\n")
    sys.exit(2)

# Chrome 132+ 删掉了经典 --headless:再传它会静默返回、PDF 根本不落地。
# 但 --headless=new 在 mac 上常丢字体,所以只有非 mac 才切新模式。
headless = "--headless" if IS_MAC else "--headless=new"
# --user-data-dir 指向临时目录:不去碰用户正在跑的 Chrome profile,否则无头实例会直接退出。
profile = tempfile.mkdtemp(prefix="md2pdf-chrome-")
cmd = [chrome, headless, "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
       "--virtual-time-budget=40000", f"--user-data-dir={profile}",
       f"--print-to-pdf={OUT}", html_path.as_uri()]  # as_uri():同样不能手拼 file://
try:
    if OUT.exists():
        try:
            OUT.unlink()  # 先删旧文件,免得把上一次的结果当成这次的成功
        except PermissionError:
            # Windows 常见:PDF 正开在 WPS/Acrobat 里,文件被锁,Chrome 写不进去。
            sys.stderr.write(f"ERROR: 目标 PDF 被其他程序占用(阅读器开着?): {OUT}\n请先关掉它再重跑。\n")
            sys.exit(4)  # finally 会清掉临时 profile
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
finally:
    shutil.rmtree(profile, ignore_errors=True)

# 必须核实文件真落地了 —— 老版本吞掉 stderr,打印失败时用户只会看到一行"成功"。
if not OUT.exists() or OUT.stat().st_size == 0:
    sys.stderr.write(f"ERROR: Chrome 退出码 {r.returncode},但没有产出 PDF: {OUT}\n")
    sys.stderr.write("命令: " + " ".join(cmd) + "\n")
    for label, stream in (("stderr", r.stderr), ("stdout", r.stdout)):
        if stream and stream.strip():
            sys.stderr.write(f"--- chrome {label} ---\n{stream.strip()}\n")
    sys.stderr.write(f"HTML 仍然可用,可手动打印: {html_path}\n")
    sys.exit(3)

print(f"PDF: {OUT}  ({OUT.stat().st_size//1024} KB, images inlined: {body.count('data:image')}, font: {font or 'system fallback'})")
