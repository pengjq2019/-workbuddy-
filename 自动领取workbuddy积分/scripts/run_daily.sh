#!/bin/bash
# WorkBuddy 每日积分领取脚本
# 由 launchd 调用

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

/usr/bin/python3 "$SCRIPT_DIR/claim_daily_credits.py"
