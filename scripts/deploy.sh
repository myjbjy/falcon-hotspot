#!/bin/bash
# 猎鹰自动部署：站点产物推送到 GitHub Pages
# 用法：bash scripts/deploy.sh（从仓库任意位置运行）
set -e
cd "$(dirname "$0")/.." || exit 1

# 只提交站点产物与数据归档（代码提交由开发阶段手动/agent 负责）
git add docs/ data/ 2>/dev/null || git add docs/ data/
if git diff --cached --quiet; then
    echo "无内容变更，跳过推送"
    exit 0
fi
git -c user.name="myjbjy" -c user.email="myjbjy@hdec.com" commit -m "🦅 猎鹰数据自动更新 $(date +%F_%H%M)" >/dev/null 2>&1
if git push origin main >/dev/null 2>&1; then
    echo "已推送到 GitHub Pages: https://myjbjy.github.io/falcon-hotspot/"
else
    echo "推送失败，请检查 git 凭据" >&2
    exit 1
fi
