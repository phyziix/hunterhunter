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
| `docs/DEPLOYMENT.md` | 部署运维手册（踩坑记录/完整步骤） |

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

## 部署

> 以下是快速摘要。完整部署步骤、踩坑记录、数据流说明见 **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**（新设备部署必读）。

- 代码仓库 ≠ 运行目录，修改后需 `cp` 到 `<PRODUCTION>/v0.1/` 并重启
- launchd 守护：FastAPI 服务 + localtunnel 隧道，两个 plist
- 公网：localtunnel（Cloudflare Tunnel 国内下载被墙）
- `static/index.html` 需单独部署，忘拷首页 404
- launchd PATH 不含 npm bin，tunnel.sh 需显式设置
- localtunnel 每 7 天需验证一次公网 IP
