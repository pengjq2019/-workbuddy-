# WorkBuddy 每日积分自动领取

自动领取 WorkBuddy "Buddy加油站" 每日赠送的 100 积分。

## 功能

- ✅ 自动读取 WorkBuddy 认证信息
- ✅ 查询签到活动状态
- ✅ 自动领取每日 100 积分
- ✅ 记录领取日志
- ✅ 支持 launchd 定时任务

## API 端点

- 签到状态: `POST https://www.codebuddy.cn/v2/billing/meter/checkin-activity-status`
- 每日签到: `POST https://www.codebuddy.cn/v2/billing/meter/daily-checkin`

## 使用方法

### 手动运行

```bash
# 查看签到状态
python3 scripts/claim_daily_credits.py --status

# 领取积分（如果今天未领取）
python3 scripts/claim_daily_credits.py

# 强制领取（忽略今日已领取标记）
python3 scripts/claim_daily_credits.py --force

# 测试模式（不实际领取）
python3 scripts/claim_daily_credits.py --test
```

### 设置定时任务（launchd）

```bash
# 安装定时任务（每天 9:00 自动领取）
cp com.workbuddy.daily-claim.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.workbuddy.daily-claim.plist

# 查看状态
launchctl list | grep workbuddy

# 立即运行一次
launchctl start com.workbuddy.daily-claim

# 卸载定时任务
launchctl unload ~/Library/LaunchAgents/com.workbuddy.daily-claim.plist
rm ~/Library/LaunchAgents/com.workbuddy.daily-claim.plist
```

### 查看日志

```bash
# 查看今日日志
cat logs/claim_$(date +%Y%m%d).log

# 查看 launchd 日志
cat logs/launchd.log
```

## 当前活动状态

- 活动名称: Buddy加油站
- 每日积分: 100
- 活动到期: 2026-08-05 10:30:00
- 连续签到: 2 天
- 总积分: 200

## 文件结构

```
├── scripts/
│   └── claim_daily_credits.py    # 主脚本
├── config/
│   └── settings.json             # 配置（记录最后领取日期）
├── logs/                         # 日志目录
├── com.workbuddy.daily-claim.plist  # launchd 配置
└── README.md
```
