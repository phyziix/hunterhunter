# v0.1 部署与配置全记录

> 记录时间：2026-05-22
> 状态：✅ 已生效

---

## 一、目录结构概览

项目涉及两个目录，需区分清楚：

| 用途 | 路径 | 说明 |
|------|------|------|
| 代码仓库 | `<WORKSPACE>/hunterhunter/` | Git 管理，源码在此 |
| 运行目录 | `<PRODUCTION>/v0.1/` | 实际服务运行位置，有独立 venv |

> **重要**：修改代码要在 `<WORKSPACE>` 下，改完后复制到 `<PRODUCTION>` 并重启服务才生效。

### 运行目录结构

```
<PRODUCTION>/v0.1/
├── main.py              # FastAPI 入口
├── engine.py            # 核心引擎
├── requirements.txt     # Python 依赖
├── tunnel.sh            # localtunnel 启动脚本
├── start.sh             # 旧版启动脚本
├── sync_to_icloud.py    # iCloud 同步脚本
├── venv/                # Python 虚拟环境
├── static/
│   └── index.html       # 前端页面（需手动部署!）
├── data/
│   └── inspire/
│       ├── Inbox/       # 灵感文件存放
│       └── _狩猎系统/   # 系统状态、配置
│           ├── state.json
│           ├── config.yaml
│           └── exchange_log.md
└── logs/
    ├── stdout.log
    ├── stderr.log
    ├── tunnel.log
    ├── tunnel_stdout.log
    └── tunnel_stderr.log
```

---

## 二、从 GitHub 部署到本地

### 1. 克隆代码

```bash
git clone <REPO_URL> <WORKSPACE>/hunterhunter
cd <WORKSPACE>/hunterhunter
git checkout v0.2    # 或其他目标分支
```

### 2. 建立运行目录

```bash
# 创建生产运行目录（与 workspace 分离）
mkdir -p <PRODUCTION>/v0.1
cp main.py engine.py requirements.txt start.sh <PRODUCTION>/v0.1/
cp -R static/ <PRODUCTION>/v0.1/static/

# 创建 Python 虚拟环境
python3 -m venv <PRODUCTION>/venv
<PRODUCTION>/venv/bin/pip install -r requirements.txt
```

### 3. 初次初始化数据目录

```bash
# 如果 data/ 还没有，手动创建
mkdir -p <PRODUCTION>/v0.1/data/inspire/Inbox
mkdir -p <PRODUCTION>/v0.1/data/inspire/_狩猎系统
mkdir -p <PRODUCTION>/v0.1/logs
```

---

## 三、灵感文件路径（核心）

`engine.py` 第 18 行决定了所有数据读写的基础路径：

```python
self.base_path = Path(__file__).parent / "data" / "inspire"
```

也就是说 **所有灵感数据都读写本地 `data/inspire/` 目录**，不是直接读写 iCloud。

### 写入位置

| 操作 | 路径 | 文件名格式 |
|------|------|-----------|
| 提交灵感 | `data/inspire/Inbox/` | `灵感-YYYY-MM-DD-HHMMSS.md` |

### 读取位置（周/月回顾）

周回顾 `_scan_notes()` 扫描的也是同一个 `data/inspire/Inbox/`，匹配 `灵感-*.md`：

```python
for file in sorted(self.inbox_folder.glob("灵感-*.md")):
```

所以 **灵感提交和回顾素材是同一个目录**，流程一致。

### 备份机制

- **触发方式**：手动（前端按钮或 `POST /api/backup`）
- **备份路径**：`~/Documents/hunterhunter_backups/inspire_backup_YYYYMMDD_HHMMSS/`
- **保留策略**：最多保留最近 10 个备份
- **无自动定时备份**，需手动触发

### iCloud 同步机制

- 应用**不直接**读写 iCloud
- 数据先存本地 `data/inspire/`，再通过 `sync_to_icloud.py` 同步到 Obsidian
- 同步目标：`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/inspire/`
- 同步策略：**只写不删**（不覆盖 Obsidian 已有文件）
- 后台定时：每 5 分钟自动同步一次（`engine.start_icloud_sync(interval=300)`）
- 也可手动触发：`POST /api/sync/icloud`
- **注意**：iCloud 云端上传由 macOS 的 iCloud Drive 守护进程处理，有数秒～数十秒延迟，属于正常现象

---

## 四、进程管理（launchd）

本服务通过两个 launchd plist 管理，均实现开机自启：

### 4.1 FastAPI 服务

plist：`~/Library/LaunchAgents/com.phyziix.hunterhunter-v0.1.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.phyziix.hunterhunter-v0.1</string>
    <key>ProgramArguments</key>
    <array>
        <string>&lt;PRODUCTION&gt;/venv/bin/python3</string>
        <string>&lt;PRODUCTION&gt;/v0.1/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>&lt;PRODUCTION&gt;/v0.1</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>&lt;PRODUCTION&gt;/v0.1/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>&lt;PRODUCTION&gt;/v0.1/logs/stderr.log</string>
</dict>
</plist>
```

### 4.2 localtunnel 隧道

plist：`~/Library/LaunchAgents/com.hunterhunter.tunnel.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hunterhunter.tunnel</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>&lt;PRODUCTION&gt;/v0.1/tunnel.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>&lt;PRODUCTION&gt;/v0.1</string>
    <key>StandardOutPath</key>
    <string>&lt;PRODUCTION&gt;/v0.1/logs/tunnel_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>&lt;PRODUCTION&gt;/v0.1/logs/tunnel_stderr.log</string>
</dict>
</plist>
```

启动脚本 `tunnel.sh`：

```bash
#!/bin/bash
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:$HOME/.npm-global/bin"

LOG_DIR="<PRODUCTION>/v0.1/logs"
mkdir -p "$LOG_DIR"
exec "$HOME/.npm-global/bin/lt" --port 8002 --subdomain <YOUR_SUBDOMAIN> >> "$LOG_DIR/tunnel.log" 2>&1
```

---

## 五、外网访问

### 方案选择

选择 **localtunnel** 而非 Cloudflare Tunnel（PRD 设计）。

原因：GitHub 下载链路不可用，`cloudflared` 二进制无法获取。

localtunnel 通过 npm 安装，国内 npmmirror 镜像可用。

### 安装

```bash
npm install -g localtunnel --registry=https://registry.npmmirror.com
# 安装后路径：$HOME/.npm-global/bin/lt
```

### 启动

```bash
lt --port 8002 --subdomain <YOUR_SUBDOMAIN>
```

外网地址：`https://<YOUR_SUBDOMAIN>.loca.lt`

### 验证清单

- [ ] 本地服务运行正常：`curl http://localhost:8002/api/status`
- [ ] localtunnel 进程在跑：`launchctl list | grep hunterhunter.tunnel`
- [ ] 外网可访问首页：`https://<YOUR_SUBDOMAIN>.loca.lt/`
- [ ] 首次访问需过验证页（输入服务器公网 IP）

---

## 六、踩坑记录

### 坑 1：代码仓库 ≠ 生产运行目录

**现象**：修改 `<WORKSPACE>/v0.1/` 下的文件不生效。

**原因**：实际运行的是 `<PRODUCTION>/v0.1/`，通过 launchd 启动。

**解决**：改完代码后需 `cp` 到生产目录并重启服务。

### 坑 2：static 目录为空 → 首页 404

**现象**：外网访问根路径 `/` 返回 `{"detail":"Not Found"}`，浏览器下载 `document.json`。

**原因**：生产环境 `static/` 目录为空，`index.html` 未随代码一起部署。

**解决**：`cp <WORKSPACE>/v0.1/static/index.html <PRODUCTION>/v0.1/static/`

### 坑 3：launchd PATH 环境变量缺失

**现象**：launchd 启动 tunnel.sh 时报 `lt: command not found`。

**原因**：launchd 默认 PATH 只有 `/usr/bin:/bin:/usr/sbin:/sbin`，不含 `node` 和 npm 全局 bin。

**解决**：在 `tunnel.sh` 开头显式设置 `PATH`，包含 `/usr/local/bin` 和 `$HOME/.npm-global/bin`。

### 坑 4：localtunnel 反滥用验证页

**现象**：首次打开外网 URL 看到一个要求输入 IP 的验证页。

**原因**：localtunnel 的反滥用机制，每个新公网 IP 每 7 天需验证一次。

**解决**：输入页面上显示的服务器公网 IP 即可通过。对个人使用可接受，多用户场景建议换成 Cloudflare Tunnel（无验证页）。

### 坑 5：Cloudflare Tunnel 安装失败

**现象**：`cloudflared` 下载一直超时。

**原因**：GitHub releases 在国内网络环境下被墙。尝试过：
- 清华源镜像（无 cloudflared）❌
- 科大源镜像（无 cloudflared）❌
- ghproxy 代理（超时）❌
- Cloudflare 官方 CDN（可解析但下载超时）❌

**后续**：网络条件允许时，建议换上 Cloudflare Tunnel——无验证页、更稳定、支持自定义域名。

### 坑 6：灵感文件「找不到」

**现象**：提交灵感后，在 Obsidian 里没立即看到。

**原因**：写入本地 → sync_to_icloud → macOS iCloud Drive 守护进程上传，有延迟。

**解决**：等待数秒到数十秒后刷新 Obsidian。属于 iCloud 同步的正常延迟。也可手动触发 `POST /api/sync/icloud` 加速同步。

---

## 七、常用命令

```bash
# ===== 进程管理 =====

# 查看所有相关进程
launchctl list | grep hunterhunter

# 重启 FastAPI 服务
launchctl unload ~/Library/LaunchAgents/com.phyziix.hunterhunter-v0.1.plist
launchctl load ~/Library/LaunchAgents/com.phyziix.hunterhunter-v0.1.plist

# 重启 tunnel
launchctl unload ~/Library/LaunchAgents/com.hunterhunter.tunnel.plist
launchctl load ~/Library/LaunchAgents/com.hunterhunter.tunnel.plist

# ===== 日志查看 =====

tail -f <PRODUCTION>/v0.1/logs/stdout.log      # 服务日志
tail -f <PRODUCTION>/v0.1/logs/tunnel.log       # tunnel 日志

# ===== 验证 =====

# 本地服务健康检查
curl http://localhost:8002/api/status

# 手动触发 iCloud 同步
curl -X POST http://localhost:8002/api/sync/icloud

# 手动触发备份
curl -X POST http://localhost:8002/api/backup

# 查看备份列表
curl http://localhost:8002/api/backup/list
```

---

## 八、关键数据流总结

```
用户提交灵感
    ↓
main.py → engine.process_daily_capture()
    ↓
写入本地 data/inspire/Inbox/灵感-YYYY-MM-DD-HHMMSS.md
    ↓ (每5分钟自动)
sync_to_icloud() → Obsidian iCloud 目录 (macOS 自动上传到云端)
    ↓
周/月回顾 → _scan_notes() 扫描 data/inspire/Inbox/灵感-*.md
    ↓
备份 → POST /api/backup → ~/Documents/hunterhunter_backups/
```
