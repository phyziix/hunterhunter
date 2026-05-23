# 项目状态

> AI 接手文档。新设备/新 AI 打开项目时，先看这个了解当前进度。
> 功能规格见 `docs/PRODUCT.md`，版本脉络见 `docs/CHANGELOG.md`，设计理念见 `docs/PHILOSOPHY.md`。
>
> ⚠️ **文档维护规则**：用户说「同步文档」时，执行以下全部操作：
> 1. 检查并更新 `CHANGELOG.md`（新版本条目 / 当前版本条目补充）
> 2. 检查并更新 `PRODUCT.md`（功能规格有变则同步）
> 3. 检查并更新 `STATUS.md`（版本号、分支、下一步有变则同步）
> 4. 检查并更新 `README.md`（版本概览表有变则同步）
> 5. **最终一步：commit 以上变更 + push**

---

## 当前版本

| 项目 | 值 |
|------|-----|
| 版本号 | 0.2.4 |
| 分支 | v0.2.4 |
| 部署状态 | 🔧 开发中，未上线 |

---

> **已上线版本**（v0.1.0、v0.1.1）见 [CHANGELOG](CHANGELOG.md)。
>
> **v0.2.4 功能规格**（10个子系统）见 [PRODUCT.md](PRODUCT.md#二v024-当前功能)。

---

## 下一步

### 优先
- [ ] **v0.2.4 生产部署**：创建 v0.2.4 launchd plist，独立于 v0.1 运行，上线
- [ ] **v0.2.5 前端拆分**：index.html 超 2200 行，CSS → styles.css，JS → app.js，HTML 仅保留结构
- [ ] **Phase 7.5 后端重构**：engine.py 按功能拆分为子模块（预估1-2天）

### 暂缓
- [ ] **Phase 8 Tab 导航**：前端 6 个 Tab(采集/概览/成长/标签/行动/规则)，Alpine.js x-show 切换

> **未来版本详情**（v0.3 赛季主题 / v0.4 自定义挑战 / v0.5 能力面板）见 `docs/PRODUCT.md#三后续版本计划`。

---

## 技术栈

- 前端：Alpine.js（单页长滚动）
- 后端：FastAPI + uvicorn
- 存储：Markdown(灵感笔记) + YAML(配置) + JSON(状态)
- 部署：launchd + localtunnel（公网）
- 仓库：github.com/phyziix/hunterhunter
