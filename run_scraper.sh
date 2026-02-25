#!/bin/bash
# Virtuals ACP Agent Scraper - 启动脚本
# 用法:
#   ./run_scraper.sh          # 单次运行
#   ./run_scraper.sh schedule # 定时运行模式

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ "$1" = "schedule" ]; then
    echo "启动定时爬虫模式..."
    python3 -m src.scheduler
else
    echo "执行单次爬取..."
    python3 -m src.main
fi
