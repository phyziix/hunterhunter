# 认知狩猎

一个"未来自我连续性训练器"，用游戏化机制辅助自律，让长期主义回报在当下可见。

## 快速启动

```bash
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

访问：http://localhost:8000

## 技术栈

- 前端：Alpine.js
- 后端：FastAPI + uvicorn
- 存储：Markdown(灵感) + YAML(配置) + JSON(状态)
- 仓库：https://github.com/phyziix/hunterhunter

## 文档

| 文件 | 用途 |
|------|------|
| `docs/PHILOSOPHY.md` | 设计理念与心理机制（只读） |
| `docs/CHANGELOG.md` | 版本发展脉络（AI 接手必读） |
| `docs/STATUS.md` | 当前进度与下一步计划 |

## 配置文件

| 文件 | 用途 |
|------|------|
| `VERSION` | 版本号（纯数字单行，如 `0.2.4`） |
| `data/inspire/_狩猎系统/config.yaml` | 运行时参数（倍率/阈值/勋章/赛季） |
| `data/inspire/_狩猎系统/defaults.yaml` | 默认配置模板（重置时参考） |
| `data/inspire/_狩猎系统/state.json` | 运行时状态（系统自动维护） |

## 版本管理

版本号在 `VERSION` 文件，纯数字单行。`main.py` 启动时自动读取。版本历史和分支对应关系见 `docs/CHANGELOG.md`。

```bash
# 发布新版本（<DEV_BRANCH> 替换为当前开发分支）
echo "X.Y.Z" > VERSION
git add VERSION
git commit -m "release: vX.Y.Z"
git tag -a vX.Y.Z -m "vX.Y.Z 上线"
git push origin <DEV_BRANCH> --tags
```

## 分支管理

```
main ─── 稳定发布版（仅合入稳定版本）
  └── <DEV_BRANCH> ─── 当前开发分支
```

| 分支 | 用途 |
|------|------|
| `main` | 稳定发布版，仅合入完整版本 |
| `<DEV_BRANCH>` | 活跃开发分支（当前所有工作在此） |
| `tag: vX.Y.Z` | 版本存档 |

### 日常操作

```bash
git clone git@github.com:phyziix/hunterhunter.git
cd hunterhunter
git checkout <DEV_BRANCH>

# 每天开始
git pull origin <DEV_BRANCH>

# 每天结束
git add -A
git commit -m "feat: 说明"
git push origin <DEV_BRANCH>

# ❌ 不要 git push origin main——main 只合入稳定版本
```

## 生产部署

### 目录结构

```
<PRODUCTION>/v0.1/          # 生产运行目录（与 workspace 分离）
├── main.py
├── engine.py
├── static/index.html
├── venv/                   # Python 虚拟环境
├── data/inspire/
│   ├── Inbox/              # 灵感文件 *.md
│   └── _狩猎系统/          # 状态/配置
└── logs/
```

**重要**：代码仓库 ≠ 运行目录。修改在 workspace 下进行，改完 cp 到 production 并重启。

### 初始化

```bash
mkdir -p <PRODUCTION>/v0.1
cp main.py engine.py requirements.txt <PRODUCTION>/v0.1/
cp -R static/ <PRODUCTION>/v0.1/static/
python3 -m venv <PRODUCTION>/v0.1/venv
<PRODUCTION>/v0.1/venv/bin/pip install -r requirements.txt
mkdir -p <PRODUCTION>/v0.1/data/inspire/Inbox
mkdir -p <PRODUCTION>/v0.1/data/inspire/_狩猎系统
mkdir -p <PRODUCTION>/v0.1/logs
```

### launchd 守护（开机自启）

FastAPI 服务 plist：`~/Library/LaunchAgents/<BUNDLE_ID>.hunterhunter-v0.1.plist`

localtunnel 隧道 plist：`~/Library/LaunchAgents/com.hunterhunter.tunnel.plist`

### localtunnel 公网访问

```bash
npm install -g localtunnel --registry=https://registry.npmmirror.com
lt --port 8002 --subdomain <YOUR_SUBDOMAIN>
# 外网地址：https://<YOUR_SUBDOMAIN>.loca.lt
```

原因：Cloudflare Tunnel 因国内 GitHub 下载链路被墙，改用 localtunnel。

### 常用命令

```bash
# 进程管理
launchctl list | grep hunterhunter
launchctl unload ~/Library/LaunchAgents/<BUNDLE_ID>.hunterhunter-v0.1.plist
launchctl load ~/Library/LaunchAgents/<BUNDLE_ID>.hunterhunter-v0.1.plist

# 日志
tail -f <PRODUCTION>/v0.1/logs/stdout.log

# 健康检查
curl http://localhost:8002/api/status

# iCloud 同步
curl -X POST http://localhost:8002/api/sync/icloud
```

### 踩坑速记

- 修改代码后需 `cp` 到 production 并重启，workspace 下的修改不直接生效
- `static/index.html` 需单独部署，忘拷会导致首页 404
- launchd 默认 PATH 不含 npm 全局 bin，tunnel.sh 需显式设置 PATH
- localtunnel 首次访问需验证服务器公网 IP（反滥用机制，每 7 天一次）
- iCloud 同步有数秒~数十秒延迟（macOS iCloud Drive 守护进程上传），属正常
