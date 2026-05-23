# 认知狩猎

一个"未来自我连续性训练器"，用游戏化机制辅助自律，让长期主义回报在当下可见。

## 快速启动

```bash
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

访问地址：http://localhost:8000

## 文档索引

- `PHILOSOPHY.md` - 底层心理机制：对抗与诱导（只读）
- `PRODUCT.md` - 产品规格说明书（v0.24，开发唯一依据）
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

项目版本号存储在根目录 `VERSION` 文件，格式 `大版本.中版本.小版本`（如 `0.2.0`）。main.py 启动时自动读取，可通过 `GET /api/version` 查询。

```bash
# 发布新版本
echo "0.2.1" > VERSION
git add VERSION
git commit -m "release: v0.2.1"
git tag -a v0.2.1 -m "v0.2.1 上线"
git push origin v0.2 --tags
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
  └── v0.24 ─── 当前开发分支（活跃开发）← 我们在这里
```

| 分支 | 用途 | 说明 |
|------|------|------|
| `main` | 稳定发布版 | 仅合入完整的稳定版本，由维护者手动合并 |
| `v0.24` | **活跃开发分支** | ✅ 当前所有开发工作在此分支进行 |
| `tag: v0.1` | 历史版本存档 | v0.1 初始版本的标记点 |

### 跨终端开发操作指南

```bash
# === 首次克隆（新设备上） ===
git clone git@github.com:phyziix/hunterhunter.git
cd hunterhunter
git checkout v0.24         # 切换到开发分支

# === 日常开发（每天开始时） ===
git pull origin v0.24      # 拉取最新代码

# === 提交代码（每天结束时） ===
git add -A
git commit -m "feat: 说明改了什么"
git push origin v0.24      # 推送到 v0.24

# === ❌ 不要这样做 ===
git push                   # 如果不在 v0.24 分支上，可能推错
git push origin main       # 不要直接推 main，main 只合入稳定版本
```

**核心规则：始终在 `v0.24` 分支上操作。** push 和 pull 都明确指定 `origin v0.24`，避免误操作 main 分支。
