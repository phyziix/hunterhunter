# 认知狩猎

一个"未来自我连续性训练器"，用游戏化机制辅助自律，让长期主义回报在当下可见。

## 快速启动

```bash
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

访问地址：http://localhost:8000

## 文档索引

- `PHILOSOPHY.md` - 底层心理机制：对抗与诱导（只读）
- `PRODUCT.md` - 产品规格说明书（开发唯一依据）
- `TECH.md` - 技术实现规格（数据结构 + API + 前端组件）
- `ROADMAP.md` - 实施路径与开发进度
- `CHANGELOG.md` - 版本变更历史
- `DEPLOYMENT.md` - 生产环境部署配置（launchd + localtunnel）

## 配置文件

| 文件 | 位置 | 用途 |
|------|------|------|
| `VERSION` | 根目录 | 项目版本号（唯一来源，部署时自增） |
| `config.yaml` | `data/inspire/_狩猎系统/config.yaml` | 运行时可调参数（倍率、阈值、勋章、赛季） |
| `defaults.yaml` | `data/inspire/_狩猎系统/defaults.yaml` | 默认配置模板（重置时参考） |
| `state.json` | `data/inspire/_狩猎系统/state.json` | 游戏运行时状态 |
| `DEPLOYMENT.md` | `docs/DEPLOYMENT.md` | 生产部署步骤（launchd 守护 + localtunnel 隧道） |

## 版本管理

项目版本号存储在根目录 `VERSION` 文件，纯数字单行（如 `0.2.4`）。`main.py` 启动时自动读取，可通过 `GET /api/version` 查询。版本历史详见 `docs/CHANGELOG.md`。

```bash
# 发布新版本（将 X.Y.Z 替换为实际版本号，<DEV_BRANCH> 替换为当前开发分支名）
echo "X.Y.Z" > VERSION
git add VERSION
git commit -m "release: vX.Y.Z"
git tag -a vX.Y.Z -m "vX.Y.Z 上线"
git push origin <DEV_BRANCH> --tags
```

## 部署方式

- **开发模式**: `python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
- **生产模式**: launchd 管理 FastAPI 进程（端口 8002），通过 localtunnel 暴露公网地址
- **公网访问**: `https://<YOUR_SUBDOMAIN>.loca.lt`（首次访问需验证 IP）
- **详细配置**: 见 [DEPLOYMENT.md](docs/DEPLOYMENT.md)

## 技术栈

- **前端**：Alpine.js
- **后端**：FastAPI
- **存储**：Markdown / JSON / YAML

## GitHub

仓库地址：https://github.com/phyziix/hunterhunter

### 分支管理

```
main ─── 稳定发布版（仅合入稳定版本）
  └── <DEV_BRANCH> ─── 当前开发分支（活跃开发）
```

> 当前开发分支名见 `VERSION` 文件对应关系（如 `0.2.4` → `v0.24`，在 `docs/CHANGELOG.md` 版本速览中可查）。

| 分支 | 用途 | 说明 |
|------|------|------|
| `main` | 稳定发布版 | 仅合入完整的稳定版本，由维护者手动合并 |
| `<DEV_BRANCH>` | **活跃开发分支** | ✅ 当前所有开发工作在此分支进行 |
| `tag: vX.Y.Z` | 版本存档 | 历史版本的 Git 标记点 |

### 跨终端开发操作指南

```bash
# === 首次克隆（新设备上） ===
git clone git@github.com:phyziix/hunterhunter.git
cd hunterhunter
git checkout <DEV_BRANCH>    # 切换到开发分支

# === 日常开发（每天开始时） ===
git pull origin <DEV_BRANCH> # 拉取最新代码

# === 提交代码（每天结束时） ===
git add -A
git commit -m "feat: 说明改了什么"
git push origin <DEV_BRANCH> # 推送到开发分支

# === ❌ 不要这样做 ===
git push                     # 可能推错分支
git push origin main         # main 只合入稳定版本
```

**核心规则**：所有操作明确指定 `origin <DEV_BRANCH>`，避免误操作 main 分支。`<DEV_BRANCH>` 替换为当前开发分支名。
