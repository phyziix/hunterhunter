# 部署与运维手册

> 记录时间：2026-05-22 / 最后维护：2026-05-25
> 状态：✅ v0.1 已下线 / ✅ v0.2.4 已下线 / ✅ v0.2.5 已下线 / ✅ v0.3.2 已下线 / ✅ v0.4.0 已下线 / ✅ v0.4.1 已上线 (8003端口) / 含 Bug #6 热修复 + iCloud 同步环境变量开关
> 
> 本文档是部署的唯一事实来源。README 的部署部分是摘要，这里才是完整步骤和踩坑记录。**新设备部署必读。**

---

## ⚠️ 部署前需确认的路径

本文档中以下占位符需替换为实际路径：

| 占位符 | 含义 | 示例 |
|--------|------|------|
| `<WORKSPACE>` | Git 代码仓库根目录 | `/Users/xxx/Documents/trae_projects` |
| `<PRODUCTION>` | 生产运行根目录 | `/Users/xxx/project/hh-online` |
| `<REPO_URL>` | GitHub 仓库地址 | `git@github.com:phyziix/hunterhunter.git` |
| `<YOUR_SUBDOMAIN>` | localtunnel 子域名 | `myapp` |
| `<BUNDLE_ID>` | launchd Bundle ID 前缀 | `com.yourname` |

> 上述路径直接影响服务能否正常启动，部署前务必确认替换。

---

## 一、目录结构概览

项目涉及两个目录，需区分清楚：

| 用途 | 路径 | 说明 |
|------|------|------|
| 代码仓库 | `<WORKSPACE>/hunterhunter/` | Git 管理，源码在此 |
| 运行目录 (当前) | `<PRODUCTION>/v0.4.1/` | **当前上线版本**，端口 8003 |
| 运行目录 (旧版) | `<PRODUCTION>/v0.4.0/` | 已下线 |
| 运行目录 (旧版) | `<PRODUCTION>/v0.3.2/` | 已下线 |
| 运行目录 (旧版) | `<PRODUCTION>/v0.2.5/` | 已下线 |
| 运行目录 (旧版) | `<PRODUCTION>/v0.2.4/` | 已下线，端口 8003 |
| 运行目录 (旧版) | `<PRODUCTION>/v0.1/` | 已下线，端口 8002 |

---

## ⚠️ 端口约定（重要）

| 用途 | 端口 | 说明 |
|------|------|------|
| 生产环境 | 8003 | **固定不变**，launchd 守护 |
| 调试环境 | 8004 | **临时使用**，避免与生产冲突 |

> 调试时需临时修改 `main.py` 端口为 8004，调试完后改回 8003。

> **重要**：修改代码要在 `<WORKSPACE>` 下，改完后复制到 `<PRODUCTION>` 并重启服务才生效。

### 运行目录结构

```
<PRODUCTION>/v0.4.1/
├── main.py              # FastAPI 入口
├── engine/              # 引擎包（Mixin 模式）
│   ├── __init__.py
│   ├── engine.py
│   ├── engine_core.py
│   ├── engine_backup.py
│   ├── engine_capture.py
│   ├── engine_exchange.py
│   ├── engine_review.py
│   └── engine_season.py
├── sync_to_icloud.py    # iCloud 同步脚本（独立）
├── VERSION              # 版本号文件
├── requirements.txt     # Python 依赖
├── tunnel.sh            # localtunnel 启动脚本
├── venv/                # Python 虚拟环境
├── static/
│   ├── index.html
│   ├── styles.css
│   └── app.js
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
```

---

## 二、从 GitHub 部署到本地

### 1. 克隆代码

```bash
git clone <REPO_URL> <WORKSPACE>/hunterhunter
cd <WORKSPACE>/hunterhunter
git checkout <目标分支>    # 如 v0.2.4
```

### 2. 建立运行目录

v0.2.4 建议使用独立目录 `<PRODUCTION>/v0.2.4/`，与旧版并行运行不冲突：

```bash
mkdir -p <PRODUCTION>/v0.2.4
cp main.py engine.py requirements.txt sync_to_icloud.py VERSION <PRODUCTION>/v0.2.4/
cp -R static/ <PRODUCTION>/v0.2.4/static/

# 创建 Python 虚拟环境
python3 -m venv <PRODUCTION>/v0.2.4/venv
<PRODUCTION>/v0.2.4/venv/bin/pip install -r requirements.txt
```

### 3. 初始化数据目录

```bash
mkdir -p <PRODUCTION>/v0.2.4/data/inspire/Inbox
mkdir -p <PRODUCTION>/v0.2.4/data/inspire/_狩猎系统
cp data/inspire/_狩猎系统/defaults.yaml data/inspire/_狩猎系统/config.yaml <PRODUCTION>/v0.2.4/data/inspire/_狩猎系统/
mkdir -p <PRODUCTION>/v0.2.4/logs
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
- **备份路径**：`~/Documents/hunterhunter_backups/hunterhunter_backup_YYYYMMDD_HHMMSS.zip`
- **备份内容**：整个 `data/` 目录
- **保留数量**：最多 30 个备份，超出自动清理

---

## 四、launchd 守护进程

### FastAPI 服务

plist 文件：`~/Library/LaunchAgents/<BUNDLE_ID>.hunterhunter-v<version>.plist`

当前 v0.4.1 关键配置：
- `WorkingDirectory`：`<PRODUCTION>/v0.4.1/`
- `ProgramArguments`：`<PRODUCTION>/v0.4.1/venv/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8003`
- `EnvironmentVariables`：`ENABLE_ICLOUD_SYNC=true`（**必须设置**，否则 iCloud 同步不会启动）
- `KeepAlive`：true
- `StandardOutPath` / `StandardErrorPath`：`<PRODUCTION>/v0.4.1/logs/`

旧版 v0.4.0 / v0.3.2 / v0.2.5 / v0.2.4 / v0.1 配置（已下线，仅供参考）：

### localtunnel 隧道

plist 文件：`~/Library/LaunchAgents/com.hunterhunter.tunnel.plist`

关键配置：
- `WorkingDirectory`：`<PRODUCTION>/v0.4.1/`
- `ProgramArguments`：`/bin/bash <PRODUCTION>/v0.4.1/tunnel.sh`
- **必须在 tunnel.sh 中显式设置 PATH**（见踩坑 3）

---

## 五、localtunnel 公网访问

```bash
npm install -g localtunnel --registry=https://registry.npmmirror.com
lt --port 8003 --subdomain <YOUR_SUBDOMAIN>
# 外网地址：https://<YOUR_SUBDOMAIN>.loca.lt
```

原因：Cloudflare Tunnel 因国内 GitHub 下载链路被墙，改用 localtunnel。

### 健康检查

部署后按顺序验证以下 5 项：

- [ ] FastAPI 服务监听端口：`curl http://localhost:8003/api/status`
- [ ] launchd 进程在跑：`launchctl list | grep hunterhunter`
- [ ] localtunnel 进程在跑：`launchctl list | grep hunterhunter.tunnel`
- [ ] 外网可访问首页：`https://<YOUR_SUBDOMAIN>.loca.lt/`
- [ ] 首次访问需过验证页（输入服务器公网 IP）

---

## 六、踩坑记录

### 坑 1：代码仓库 ≠ 生产运行目录

**现象**：修改 `<WORKSPACE>/hunterhunter/` 下的文件不生效。

**原因**：实际运行的是 `<PRODUCTION>/v0.1/`，通过 launchd 启动。

**解决**：改完代码后需 `cp` 到生产目录并重启服务。

### 坑 2：static 目录为空 → 首页 404

**现象**：外网访问根路径 `/` 返回 `{"detail":"Not Found"}`，浏览器下载 `document.json`。

**原因**：生产环境 `static/` 目录为空，`index.html` 未随代码一起部署。

**解决**：`cp <WORKSPACE>/hunterhunter/static/index.html <PRODUCTION>/v0.1/static/`

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

### 坑 7：v0.2.5 标签查询 KeyError — tag_index 迁移遗漏

**现象**：生产环境点击标签或提交笔记时报 `KeyError: 'tag_index'`。

**原因**：v0.3.1 新增了 `tag_index`（标签→笔记文件路径的 O(1) 索引），代码多处直接 `self.state["tag_index"]` 访问，但 `_migrate_state_v022` 的 `required_fields` 列表遗漏了 `tag_index`。生产 state.json 没有该字段，迁移跳过，运行时报错。

**解决**：在 `engine.py` 的 `required_fields` 中加入 `"tag_index"`，重启后自动迁移补齐字段。修复已在 workspace v0.3.2-dev 的 `engine/engine_core.py` 和生产 v0.2.5 的 `engine.py` 同步应用。

---

## 七、常用命令

```bash
# ===== 进程管理 =====

# 查看所有相关进程
launchctl list | grep hunterhunter

# 重启 FastAPI 服务 (v0.2.5)
launchctl unload ~/Library/LaunchAgents/<BUNDLE_ID>.hunterhunter-v0.2.5.plist
launchctl load ~/Library/LaunchAgents/<BUNDLE_ID>.hunterhunter-v0.2.5.plist

# 重启 tunnel
launchctl unload ~/Library/LaunchAgents/com.hunterhunter.tunnel.plist
launchctl load ~/Library/LaunchAgents/com.hunterhunter.tunnel.plist

# ===== 日志查看 =====

tail -f <PRODUCTION>/v0.2.5/logs/stdout.log      # 服务日志
tail -f <PRODUCTION>/v0.2.5/logs/stderr.log      # 错误日志

# ===== 验证 =====

# 本地服务健康检查
curl http://localhost:8003/api/status

# 手动触发 iCloud 同步
curl -X POST http://localhost:8003/api/sync/icloud

# 手动触发备份
curl -X POST http://localhost:8003/api/backup

# 查看备份列表
curl http://localhost:8003/api/backup/list
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
