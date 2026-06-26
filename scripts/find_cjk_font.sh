#!/usr/bin/env bash
# 打印一个可用的「单文件」CJK 字体路径(ttf/otf 优先,ttc 兜底)。
# 无头浏览器靠 @font-face 加载它来渲染中文;.ttc 字体集合常加载失败,故优先单文件。
for f in \
  "/System/Library/Fonts/Supplemental/Arial Unicode.ttf" \
  "/Library/Fonts/Arial Unicode.ttf" \
  "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf" \
  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf" \
  "/usr/share/fonts/truetype/arphic/uming.ttc" \
  "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc" \
  "/System/Library/Fonts/Supplemental/Songti.ttc" \
  "/System/Library/Fonts/STHeiti Light.ttc" \
  "/System/Library/Fonts/PingFang.ttc" ; do
  [ -f "$f" ] && { echo "$f"; exit 0; }
done
exit 1
