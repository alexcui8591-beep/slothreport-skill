#!/usr/bin/env bash
# slothreport 前置安装(幂等,装过会跳过)。
# 装:poppler(抠图 PDF→PNG / 渲染校验)、python-markdown(md→html)、
#    可选 matplotlib/numpy/pandas(重画图表)、arxiv-latex-mcp(精确取公式)。
# 出 PDF 还需要一个 Chromium 内核浏览器(mac 上通常已有 Google Chrome)。
set -uo pipefail
say(){ printf "\033[1;36m::\033[0m %s\n" "$*"; }
ok(){ printf "  \033[32m✓\033[0m %s\n" "$*"; }
warn(){ printf "  \033[33m!\033[0m %s\n" "$*"; }

OS="$(uname -s)"
say "OS = $OS"

# ---- 1) poppler (pdftoppm/pdftocairo) ----
if command -v pdftoppm >/dev/null 2>&1; then ok "poppler 已装"; else
  say "装 poppler ..."
  if [ "$OS" = Darwin ]; then brew install poppler
  elif command -v apt-get >/dev/null 2>&1; then sudo apt-get install -y poppler-utils
  elif command -v dnf >/dev/null 2>&1; then sudo dnf install -y poppler-utils
  else warn "未知包管理器,请手动装 poppler-utils"; fi
  command -v pdftoppm >/dev/null 2>&1 && ok "poppler 就绪" || warn "poppler 装失败"
fi

# ---- 2) python markdown (必需,md→html) ----
PY="$(command -v python3 || command -v python)"
if "$PY" -c "import markdown" 2>/dev/null; then ok "python-markdown 已装"; else
  say "装 python-markdown ..."; "$PY" -m pip install --user --quiet markdown && ok "markdown 就绪" || warn "markdown 装失败"
fi

# ---- 3) 可选:重画图表用 ----
if "$PY" -c "import matplotlib,numpy,pandas" 2>/dev/null; then ok "matplotlib/numpy/pandas 已装(可重画图表)"; else
  say "装 matplotlib/numpy/pandas(可选,重画图表用)..."
  "$PY" -m pip install --user --quiet matplotlib numpy pandas && ok "图表依赖就绪" || warn "图表依赖未装(不影响默认流程)"
fi

# ---- 4) 可选:arxiv-latex-mcp(精确取公式 LaTeX 源)----
if command -v arxiv-latex-mcp >/dev/null 2>&1; then ok "arxiv-latex-mcp 已装"
elif command -v uv >/dev/null 2>&1; then
  say "装 arxiv-latex-mcp(精确取公式)..."; uv tool install arxiv-latex-mcp >/dev/null 2>&1 && ok "arxiv-latex-mcp 就绪(MCP 需重启会话才生效)" || warn "arxiv-latex-mcp 装失败(可跳过,改用本地源码包)"
else warn "无 uv,跳过 arxiv-latex-mcp(改用下载 e-print 源码包取公式)"; fi

# ---- 5) 出 PDF 需要的浏览器(只检测,不强装)----
# Windows(Git Bash/MSYS)下 Chrome 和 Edge 都行,两者同为 Chromium 内核。
CHROME=""
for c in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
         "/Applications/Chromium.app/Contents/MacOS/Chromium" \
         "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
         "/c/Program Files/Google/Chrome/Application/chrome.exe" \
         "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" \
         "/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
         "$(command -v google-chrome 2>/dev/null)" "$(command -v chromium 2>/dev/null)"; do
  [ -n "$c" ] && [ -x "$c" ] && CHROME="$c" && break
done
[ -n "$CHROME" ] && ok "浏览器(出 PDF):$CHROME" || warn "未发现 Chrome/Chromium/Edge —— 出 PDF 需要它,请装一个;否则只出 markdown"

# ---- 6) CJK 字体(mac/Linux 出 PDF 必需,那里的无头浏览器读不到系统字体)----
# Windows 例外:Chrome 会走系统字体回退,找不到单文件字体也不影响中文。
if "$(dirname "$0")/find_cjk_font.sh" >/dev/null 2>&1; then
  ok "找到可用 CJK 字体(出 PDF)"
elif [ "${OS#MINGW}" != "$OS" ] || [ "${OS#MSYS}" != "$OS" ] || [ "${OS#CYGWIN}" != "$OS" ]; then
  ok "未找到单文件 CJK 字体,但 Windows 上 Chrome 会用系统字体回退,中文正常"
else
  warn "未找到单文件 CJK 字体,中文 PDF 可能空白(见 visuals_and_tools.md)"
fi

say "完成。默认出 markdown 零依赖;出 PDF 需 浏览器 + CJK 字体。"
