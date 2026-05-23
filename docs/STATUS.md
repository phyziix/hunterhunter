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
>
> ⚠️ **调试规则**：用户说「调试」或贴了报错截图时，执行以下全部操作：
> 1. **启动运行时环境**：`python3 main.py &` 启动后端 + `playwright-cli open` 打开浏览器
> 2. 区分来源：Console 红字 → 前端问题；Network 红请求 → 后端问题
> 3. 同时自查代码一致性（API 路由与函数签名是否匹配、state.json 结构是否与文档一致、config.yaml 键是否被正确引用）
> 4. 给出本次变更的验收清单（3-7 条可操作检查项）
> 5. 异常时列出问题并给出修复；无异常则说「调试通过」
> 6. **最后一步**：停服、删 playwright-cli 临时目录、删测试产生的笔记/星点，恢复测试前的 state.json

---

## 当前版本

| 项目 | 值 |
|------|-----|
| 版本号 | 0.2.4 |
| 分支 | v0.2.4 |
| 部署状态 | ✅ 已上线 (8003端口 + hunterhub.loca.lt) |

---

> **已上线版本**（v0.1.0、v0.1.1）见 [CHANGELOG](CHANGELOG.md)。
>
> **v0.2.4 功能规格**（10个子系统）见 [PRODUCT.md](PRODUCT.md#二v024-当前功能)。

---

## 下一步

### 优先
- [x] **v0.2.4 生产部署**：创建 v0.2.4 launchd plist，独立于 v0.1 运行，上线
- [ ] **v0.2.5 前端拆分**：index.html 超 2600 行，CSS → styles.css，JS → app.js，HTML 仅保留结构
- [ ] **v0.3 后端重构**：engine.py 按功能拆分为子模块（预估1-2天）

### 暂缓
- [ ] **v0.4 赛季主题**：开拓者/连线大师/深度矿工/分享者 四主题 + **方案B**：app.js 按模块拆分（capture/exchange/review）
- [ ] **v0.5 自定义挑战**：用户自行设定挑战目标与奖励，自动追踪进度
- [ ] **v0.6 能力值面板**：星点里程碑档位制 + 前端能力面板展示
- [ ] **v0.7 Tab 导航**：前端 6 个 Tab(采集/概览/成长/标签/行动/规则)，Alpine.js x-show 切换
- [ ] **AI_WORKFLOW.md 拆分**：触发条件（任一满足时执行）→ 规则超过 5 条 / 某条超 10 行 / STATUS 超 100 行。将顶部 ⚠️ 操作规则移出到独立文件，STATUS 恢复纯状态文档

---

## 技术栈

- 前端：Alpine.js（单页长滚动）
- 后端：FastAPI + uvicorn
- 存储：Markdown(灵感笔记) + YAML(配置) + JSON(状态)
- 部署：launchd + localtunnel（公网）
- 仓库：github.com/phyziix/hunterhunter
