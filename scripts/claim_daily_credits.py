#!/usr/bin/env python3
"""
WorkBuddy 每日积分自动领取脚本
API: POST /v2/billing/meter/daily-checkin
状态查询: POST /v2/billing/meter/checkin-activity-status

使用方法:
  python3 claim_daily_credits.py
  python3 claim_daily_credits.py --force    # 强制领取（忽略今日已领取标记）
  python3 claim_daily_credits.py --status   # 仅查看签到状态
  python3 claim_daily_credits.py --test     # 测试模式（不实际领取）
"""

import json
import os
import sys
import urllib.request
import urllib.error
import argparse
from datetime import datetime
from pathlib import Path

# 配置
WORKBUDDY_AUTH_PATH = Path.home() / "Library/Application Support/CodeBuddyExtension/Data/Public/auth/workbuddy-desktop.info"
API_BASE_URL = "https://www.codebuddy.cn"
LOG_DIR = Path(__file__).parent.parent / "logs"
CONFIG_FILE = Path(__file__).parent.parent / "config" / "settings.json"

# API 端点
CHECKIN_STATUS_URL = f"{API_BASE_URL}/v2/billing/meter/checkin-activity-status"
DAILY_CHECKIN_URL = f"{API_BASE_URL}/v2/billing/meter/daily-checkin"


def load_auth():
    """从 WorkBuddy 应用数据目录加载认证信息"""
    if not WORKBUDDY_AUTH_PATH.exists():
        raise FileNotFoundError(f"认证文件不存在：{WORKBUDDY_AUTH_PATH}")

    with open(WORKBUDDY_AUTH_PATH, 'r') as f:
        auth_data = json.load(f)

    return auth_data.get('auth', {})


def load_config():
    """加载配置文件"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_config(config):
    """保存配置文件"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def log(message, level="INFO"):
    """记录日志"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)

    log_file = LOG_DIR / f"claim_{datetime.now().strftime('%Y%m%d')}.log"
    with open(log_file, 'a') as f:
        f.write(log_line + "\n")


def make_api_request(url, token, data=None):
    """发送 API 请求"""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    body = json.dumps(data).encode('utf-8') if data is not None else b'{}'
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='replace')
        try:
            return e.code, json.loads(error_body)
        except json.JSONDecodeError:
            return e.code, {"error": error_body}
    except urllib.error.URLError as e:
        return None, {"error": f"网络错误：{e.reason}"}
    except Exception as e:
        return None, {"error": str(e)}


def get_checkin_status(token):
    """获取签到活动状态"""
    log("正在获取签到状态...")
    status, response = make_api_request(CHECKIN_STATUS_URL, token)

    if status == 200 and response.get("code") == 0:
        data = response.get("data", {})
        log(f"活动状态: active={data.get('active')}")
        log(f"今日已签到: {data.get('today_checked_in')}")
        log(f"连续签到: {data.get('streak_days')} 天")
        log(f"每日积分: {data.get('daily_credit')}")
        log(f"总积分: {data.get('total_credits')}")
        log(f"活动名称: {data.get('theme_name', 'N/A')}")
        log(f"活动到期: {data.get('end_time', 'N/A')}")
        return data
    else:
        log(f"获取状态失败: {response}", "ERROR")
        return None


def claim_daily_checkin(token, dry_run=False):
    """执行每日签到领取积分"""
    log("正在尝试领取每日积分...")

    if dry_run:
        log("[测试模式] 跳过实际领取请求", "WARNING")
        return {"dry_run": True, "message": "测试模式，未实际领取"}

    status, response = make_api_request(DAILY_CHECKIN_URL, token)

    if status == 200 and response.get("code") == 0:
        data = response.get("data", {})
        log(f"✅ 领取成功！获得 {data.get('daily_credit', 100)} 积分")
        return {"success": True, "data": data}
    elif status == 400 and response.get("code") == 10001:
        log("今天已经领取过积分了，明天再来吧~", "INFO")
        return {"success": False, "already_claimed": True, "message": response.get("msg", "")}
    else:
        log(f"领取失败: {response}", "ERROR")
        return {"success": False, "error": response}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='WorkBuddy 每日积分自动领取')
    parser.add_argument('--force', action='store_true', help='强制领取（忽略今日已领取标记）')
    parser.add_argument('--status', action='store_true', help='仅查看签到状态')
    parser.add_argument('--test', action='store_true', help='测试模式（不实际领取）')
    args = parser.parse_args()

    log("=" * 50)
    log("WorkBuddy 每日积分领取脚本启动")

    # 加载认证信息
    try:
        auth_info = load_auth()
        token = auth_info.get('accessToken')
        if not token:
            log("无法获取访问令牌，请重新登录 WorkBuddy", "ERROR")
            return 1
        log("认证信息加载成功")
    except Exception as e:
        log(f"加载认证信息失败：{e}", "ERROR")
        return 1

    # 状态查询模式
    if args.status:
        data = get_checkin_status(token)
        if data:
            print("\n" + "=" * 50)
            print("📊 签到状态摘要")
            print("=" * 50)
            print(f"  活动状态: {'✅ 进行中' if data.get('active') else '❌ 已结束'}")
            print(f"  今日领取: {'✅ 已领取' if data.get('today_checked_in') else '⏳ 未领取'}")
            print(f"  连续签到: {data.get('streak_days')} 天")
            print(f"  每日积分: {data.get('daily_credit')} 积分")
            print(f"  总积分: {data.get('total_credits')} 积分")
            print(f"  活动名称: {data.get('theme_name', 'N/A')}")
            print(f"  活动到期: {data.get('end_time', 'N/A')}")
            if data.get('checkin_dates'):
                print(f"  签到记录: {', '.join(data['checkin_dates'])}")
        return 0

    # 检查今天是否已经领取过
    config = load_config()
    last_claim_date = config.get('last_claim_date', '')
    today = datetime.now().strftime('%Y-%m-%d')

    if not args.force and last_claim_date == today:
        log(f"今天 ({today}) 已经领取过积分，跳过")
        return 0

    # 先获取签到状态
    status_data = get_checkin_status(token)
    if not status_data:
        log("无法获取签到状态，脚本退出", "ERROR")
        return 1

    # 如果活动未开始或已结束
    if not status_data.get('active'):
        log("当前没有进行中的签到活动", "WARNING")
        return 0

    # 如果今天已经领取过
    if status_data.get('today_checked_in') and not args.force:
        log(f"今天已经领取过积分（连续签到 {status_data.get('streak_days')} 天）", "INFO")
        config['last_claim_date'] = today
        save_config(config)
        return 0

    # 执行领取
    dry_run = args.test
    result = claim_daily_checkin(token, dry_run=dry_run)

    if result.get("success"):
        log("✅ 每日积分领取完成！")
        config['last_claim_date'] = today
        config['last_streak'] = status_data.get('streak_days', 0)
        save_config(config)
        return 0
    elif result.get("already_claimed"):
        log("今天已经领取过积分了", "INFO")
        config['last_claim_date'] = today
        save_config(config)
        return 0
    else:
        log(f"领取失败: {result.get('error', '未知错误')}", "ERROR")
        return 1


if __name__ == "__main__":
    sys.exit(main())
