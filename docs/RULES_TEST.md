# 系统规则与开关条件清单

> 记录当前系统中所有规则、开关条件、配置项及其状态。
> 生成时间：2026-05-25 | v0.4.1-dev

---

## 目录

1. [已配置的开关/条件](#已配置的开关条件)
2. [已实现但未配置化的规则](#已实现但未配置化的规则)
3. [建议新增的开关/条件](#建议新增的开关条件)
4. [测试验证清单](#测试验证清单)
5. [配置化优先级建议](#配置化优先级建议)

---

## 一、已配置的开关/条件

| 规则类型 | 配置项 | 值 | 位置 | 说明 |
|---------|--------|-----|------|------|
| **模块开关** | `ENABLE_EXCHANGE` | `true` | `main.py:33` | 兑换模块总开关（环境变量） |
| **兑换规则** | `fund.min_withdraw` | `500` | `config.yaml:36` | 基金最低兑换额度（星点） |
| **采集规则** | `daily_multipliers` | `[1.0, 1.5, 2.0, 0.2]` | `config.yaml:27-31` | 每日采集倍率阶梯 |
| **连续加成** | `streak_bonuses` | `7天+10%, 30天+30%, 90天+50%` | `config.yaml:94-100` | 连续采集加成 |
| **路径奖励** | `path_bonuses` | 基金+消费连续奖励 | `config.yaml:68-82` | 连续选择同一路径的奖励/惩罚 |
| **周回顾** | `weekly_review_reward` | `200` | `config.yaml:101` | 周回顾奖励星点 |
| **月度战报** | `monthly_report_reward` | `500` | `config.yaml:67` | 月度战报奖励星点 |
| **内容发布** | `content_output_max_times` | `5` | `config.yaml:22` | 每月最大发布次数 |
| **内容发布** | `content_output_reward_min/max` | `750-1000` | `config.yaml:23-24` | 发布奖励范围 |
| **重复检测** | `_check_duplicate` | `相似度>85%` | `engine_capture.py:339` | 重复提交检测（硬编码） |
| **勋章系统** | `medals` | 4个勋章配置 | `config.yaml:39-65` | 条件触发式勋章 |
| **赛季配置** | `seasons.default_length_days` | `15` | `config.yaml:86` | 赛季天数 |
| **赛季配置** | `seasons.auto_start` | `true` | `config.yaml:85` | 自动开启新赛季 |
| **跨界采集** | `cross_domain_bonus` | `5` | `config.yaml:11` | 跨领域采集加成（星点） |
| **连接力奖励** | `link_power_rewards` | 3个阈值 | `config.yaml:14-20` | 连接力达到阈值奖励 |
| **赛季限制** | `season_star_cap` | `3000` | `config.yaml:6` | 赛季星点上限 |
| **赛季重置** | `season_soft_reset_ratio` | `0.5` | `config.yaml:7` | 赛季结算保留比例 |
| **基础星点** | `base_star` | `10` | `config.yaml:8` | 单次采集基础星点 |

---

## 二、已实现但未配置化的规则

| 规则 | 当前状态 | 位置 | 建议 |
|------|---------|------|------|
| **赛季模块开关** | 硬编码关闭 | `engine_core.py` | 添加 `ENABLE_SEASON` 环境变量 |
| **重复提交检测阈值** | 硬编码 85% | `engine_capture.py:373` | 添加配置项 `duplicate_threshold` |
| **连续加成开关** | 无开关 | `engine_capture.py` | 添加配置项 `streak_bonus_enabled` |
| **跨界采集开关** | 无开关 | `engine_capture.py` | 添加配置项 `cross_domain_bonus_enabled` |
| **连接力奖励开关** | 无开关 | `engine_core.py` | 添加配置项 `link_power_reward_enabled` |

---

## 三、建议新增的开关/条件

| 开关名称 | 建议值 | 用途 | 建议位置 |
|---------|--------|------|---------|
| `ENABLE_SEASON` | `false` | 赛季模块开关（当前已下线） | `main.py`（环境变量） |
| `DUPLICATE_CHECK_ENABLED` | `true` | 重复提交检测开关 | `config.yaml` |
| `DUPLICATE_THRESHOLD` | `0.85` | 重复检测相似度阈值 | `config.yaml` |
| `STREAK_BONUS_ENABLED` | `true` | 连续采集加成开关 | `config.yaml` |
| `CROSS_DOMAIN_BONUS_ENABLED` | `true` | 跨界采集加成开关 | `config.yaml` |
| `LINK_POWER_REWARD_ENABLED` | `true` | 连接力奖励开关 | `config.yaml` |

---

## 四、测试验证清单（v0.4.1）

### 采集相关
| 测试项 | 验证方法 | 预期结果 |
|--------|---------|---------|
| 重复提交检测 | 提交相似度 >85% 的内容 | 返回错误：存在高度相似的笔记 |
| 每日采集倍率 | 第1/2/3/4次采集 | 星点分别为 10/15/20/2 |
| 连续加成 | 连续采集7/30/90天后 | 加成 10%/30%/50% |
| 跨界采集加成 | 提交含≥2个不同领域标签的笔记 | 额外+5星点 |

### 兑换相关
| 测试项 | 验证方法 | 预期结果 |
|--------|---------|---------|
| 基金最低额度 | 尝试兑换 <500 星点 | 返回错误：基金兑换最低额度为500星点 |
| 兑换模块开关 | 设置 `ENABLE_EXCHANGE=false` | 兑换接口返回 403 |
| 路径连续奖励 | 连续选择基金/消费8周 | 基金+15%，消费-15% |

### 回顾相关
| 测试项 | 验证方法 | 预期结果 |
|--------|---------|---------|
| 周回顾次数 | 一周内多次提交 | 每周限1次 |
| 周回顾奖励 | 提交周回顾 | 获得200星点 |
| 月度战报奖励 | 提交月度战报 | 获得500星点 |

### 内容发布
| 测试项 | 验证方法 | 预期结果 |
|--------|---------|---------|
| 发布次数限制 | 一个月内发布6次 | 第6次返回错误 |
| 发布奖励范围 | 发布不同长度内容 | 获得750-1000星点 |

---

### 测试结果（2026-05-25，v0.4.1-dev，8004端口）

> **第一轮**：真实数据测试。**第二轮**：构造虚拟历史数据补充测试（标记 🧪）。

#### 采集相关

| 测试项 | 结论 | 详情 |
|--------|------|------|
| 重复提交检测 | ❌ Bug | 完全相同可拒绝，但高度相似（末尾加一句话）可绕过。根因：`_check_duplicate` 用位置逐字匹配（`normalized[i] == existing_normalized[i]`），不是真正的文本相似度算法。前缀稍有不同即导致窗口全错位，相似度远低于 85% |
| 每日采集倍率 | ✅ 通过 | 第1次=10 / 第2次=15 / 第3次=20 / 第4-5次=2，完全符合 `[1.0, 1.5, 2.0, 0.2]` |
| 连续加成（7天+10%）| ✅ 通过 🧪 | 修改 state 设 `streak_days=7`，第1次采集 earned=11.0（base=10 + 10%=1），正确 |
| 跨界采集加成 | ❌ 未实现 | `cross_domain_bonus: 5` 配置存在但 `_calculate_stars()` 从未调用，无跨领域检测逻辑 |

#### 兑换相关

| 测试项 | 结论 | 详情 |
|--------|------|------|
| 基金最低额度（<500拒绝）| ✅ 通过 🧪 | 清除 `last_exchange_date` 后，兑换 300 返回 `detail: 基金兑换最低额度为 500 星点`，正确拒绝 |
| 基金路径连续奖励（8周）| ✅ 通过 🧪 | `path_streak_weeks=8`，汇率 = base_rate(1.0) + base_bonus(0.5) + path(0.05+0.10+0.15) = 1.80，500×1.80=900，正确（注：path_bonus 各阶梯为累加关系） |
| 兑换模块开关 | ✅ 通过 🧪 | `ENABLE_EXCHANGE=false` 重启后，兑换返回 `detail: 兑换模块已临时关闭`，正确拒绝 |

#### 回顾相关

| 测试项 | 结论 | 详情 |
|--------|------|------|
| 周回顾生成（查上周笔记）| ✅ 通过 🧪 | 构造 3 条上周笔记，生成素材正确找到 3 条 |
| 周回顾提交奖励 | ✅ 通过 🧪 | 首次提交获得 200 星点 |
| **周回顾重复提交** | ❌ **Bug** 🧪 | `submit_weekly_review()` 缺少 `weekly_review_done` 检查，可重复提交并获得多次奖励。`generate_weekly_review()` 有拦截但 `submit` 没有 |
| 月度战报生成（查上月笔记）| ✅ 通过 🧪 | 构造 2 条四月笔记，生成素材正确找到 2 条 |
| 月度战报提交奖励 | ✅ 通过 🧪 | 提交获得 500 星点 |

#### 内容发布

| 测试项 | 结论 | 详情 |
|--------|------|------|
| 发布次数限制 | ✅ 通过 | 第5次被拒「已达到最大发布次数（5次）」 |
| 发布奖励范围 | ✅ 通过 | reward=960，在 750-1000 区间内 |

#### 总结

| 类别 | ✅ 通过 | ❌ Bug | ❌ 未实现 |
|------|--------|--------|-----------|
| 采集 | 3 | 1 | 1 |
| 兑换 | 3 | 0 | 0 |
| 回顾 | 4 | 1 | 0 |
| 内容发布 | 2 | 0 | 0 |
| **合计** | **12** | **2** | **1** |

**核心发现：**
1. **重复检测是位置匹配而非文本相似度** — 前缀稍有不同即绕过 85% 阈值
2. **跨界采集加成从未上线** — 配置项有，`_calculate_stars()` 没调
3. **周回顾可重复提交** — `submit_weekly_review()` 缺少 `weekly_review_done` 守卫，`generate` 有但 `submit` 没有
4. 每日倍率、连续加成、兑换门槛、路径奖励、回顾奖励、内容发布限制均正确

#### 第三轮：清单外在线项补充测试（2026-05-25）

> 对照 STATUS.md，排除赛季（已下线）和跨界采集（未实现），补测 5 项。

| # | 测试项 | 结论 | 详情 |
|---|--------|------|------|
| 1 | **消费路径兑换（连续惩罚）** | ❌ **Bug** | `_calculate_exchange_rate()` 的 else 分支直接返回 `coupon_rate`，从未调用 `_calculate_path_streak_bonus("coupon")`。state 中所有 coupon 兑换 `real_value==amount`（汇率=1.0），8 周惩罚 -0.15 完全未生效 |
| 2 | 连续加成 30天+30% | ✅ 通过 🧪 | 设 `streak_days=30`，采集 earned=13.0（base=10 + 30%=13），正确 |
| 3 | 连续加成 90天+50% | ✅ 通过 🧪 | 设 `streak_days=90`，采集 earned=15.0（base=10 + 50%=15），正确 |
| 4 | **月度战报重复提交** | ❌ **Bug** | `submit_monthly_report()` 缺少 `monthly_report_done` 检查，可重复提交。state 中已有 2 笔 `月度战报 500` 收入记录，证实可刷星点 |
| 5a | 勋章「周常猎人」（weekly_review_streak≥4）| ✅ 通过 | 设 `weekly_review_streak=4`，采集后静默触发了勋章（state.medals 已记录）。但 `process_daily_capture()` 丢弃了 `_check_medals()` 返回值，采集响应中缺少 `new_medals` 字段，前端无法实时获知 |
| 5b | 勋章重复触发防护 | ✅ 通过 | 恢复已获得勋章后再次 check，无重复触发 |
| 5c | 连接力奖励 threshold=5, 20 | ✅ 通过 | 清空 `link_power_rewards_earned` 后，采集正确触发 50+100 星点奖励 |
| 5d | 连接力奖励 threshold=50 | ⚠️ 无法测 | `_calculate_link_power()` 在采集时重新计算，当前图数据下 link_power≈27，无法达到 50。需大量高密度笔记才能自然触发。代码逻辑与 5/20 一致，理论正确 |

#### 边界值补充测试（2026-05-25）

| 测试项 | 结论 | 详情 |
|--------|------|------|
| 每日倍率第 100 次 | ✅ 通过 | `today_count=99→100`，正确取 `multipliers[-1]=0.2`，earned=2.0，无数组越界 |
| 连续加成 6 天边界 | ✅ 通过 | `streak_days=6` + 今日采集 → `_check_streak()` 递增至 7 → 正确触发 10% 加成（6天历史+今天=第7天，逻辑正确） |
| 基金正好 500（边界值） | ✅ 通过 | `min_withdraw=500`，兑换 500 成功，real_value=750（汇率 1.5），边界值 `>=` 判断正确 |

#### 第三轮总结

| 类别 | ✅ 通过 | ❌ Bug | ⚠️ 无法测 |
|------|--------|--------|-----------|
| 消费路径 | 0 | 1 | 0 |
| 连续加成 | 2 | 0 | 0 |
| 月度战报 | 0 | 1 | 0 |
| 勋章系统 | 2 | 0 | 0 |
| 连接力奖励 | 1 | 0 | 1 |
| **合计** | **5** | **2** | **1** |

**新发现 Bug：**
1. **消费路径连续惩罚从未生效** — `_calculate_exchange_rate` else 分支未调用 `_calculate_path_streak_bonus`
2. **月度战报可重复提交** — 与周回顾同类 Bug，`submit_monthly_report()` 缺少 `monthly_report_done` 守卫

**次要发现：**
- `process_daily_capture()` 丢弃了 `_check_medals()` 返回值，采集 API 响应中缺少 `new_medals` 字段

**累计 Bug 清单（三轮合计）：**

| # | Bug | 严重度 | 位置 | 状态 |
|---|-----|--------|------|:----:|
| 1 | 重复检测是位置匹配而非文本相似度 | 中 | `engine_capture.py:_check_duplicate` | ⏳ 暂缓 |
| 2 | 跨界采集加成从未上线 | 低 | `engine_capture.py:_calculate_stars` | ⏳ 暂缓 |
| 3 | 周回顾可重复提交 | 高 | `engine_review.py:submit_weekly_review` | ✅ 已修复 |
| 4 | 消费路径连续惩罚从未生效 | 中 | `engine_exchange.py:_calculate_exchange_rate` | ✅ 已修复 |
| 5 | 月度战报可重复提交 | 高 | `engine_review.py:submit_monthly_report` | ✅ 已修复 |

#### Bug 修复记录（2026-05-25）

| # | 修复内容 | 文件 | 改动 |
|---|---------|------|------|
| 3 | `submit_weekly_review()` 增加 `weekly_review_done` 守卫 | `engine_review.py:289-290` | 与 `generate_weekly_review` 同款拦截，已提交则拒绝 |
| 4 | `_calculate_exchange_rate()` else 分支补 `_calculate_path_streak_bonus("coupon")` | `engine_exchange.py:49` | 消费路径的连续惩罚（2/4/8周 -0.05/-0.10/-0.15）现在生效 |
| 5 | `submit_monthly_report()` 增加 `monthly_report_done` 守卫 | `engine_review.py:358-359` | 与 Bug #3 同类修复，已提交则拒绝 |

#### 第四轮：API 全覆盖 + 勋章完整性 + 路径边界 + 周期重置（2026-05-25）

> 对照 main.py 全部 31 个 API 端点逐条对账，补测前三轮遗漏的端点和规则。

##### P0：核心功能缺口

| # | 测试项 | 结论 | 详情 |
|---|--------|------|------|
| 1 | `POST /api/exchange/path` 设置兑换路径 | ⚠️ **新 Bug** | 基本功能正常（fund/coupon 切换、无效路径拒绝），但 `_update_path_streak()` 中 `last_choice`（周字符串如 "2026-21"）与 `path`（路径名 "fund"/"coupon"）比较永远不等，**path_streak_weeks 永远不会通过 API 正常累积**，始终为 0 |
| 2a | `POST /api/consume` 记录消费 | ✅ 通过 | 正常记录、余额递减正确 |
| 2b | 消费超额保护 | ✅ 通过 | 额度不足时返回 400 + 剩余额度提示 |
| 2c | `GET /api/consume/history` 消费历史 | ✅ 通过 | 返回 consumed_amount / coupon_pool / remaining / records |
| 3 | `PUT /api/config` 配置持久化 | ✅ 通过 | 修改 base_star=15 → 重启 → 仍为 15，`_save_config()` 写 yaml 正确 |

##### P1：勋章系统完整性

| # | 勋章 | 结论 | 详情 |
|---|------|------|------|
| 4 | 💡 灵光乍现 (first_triple) | ✅ 通过 | 早期测试轮次已触发（today_count≥3），已 earned |
| 5 | 🕸️ 连线大师 (link_master) | ✅ 通过 | 月度战报标签≥3 正确触发（构造上月 3 条多标签笔记 → submit → `_last_report_tag_count=3` → 勋章激活） |
| 6 | 🔗 连线新手 (link_novice) | ✅ 通过 | 早期测试轮次已触发（link_power≥5），已 earned |

##### P2：路径交换边界

| # | 测试项 | 结论 | 详情 |
|---|--------|------|------|
| 7 | 基金路径 2周(+0.05→1.55) / 4周(+0.10→1.65) | ✅ 通过 | 状态注入验证，各级累加正确（注：因 Bug #6 无法自然累积） |
| 8 | 消费路径 2周(-0.05→0.95) / 4周(-0.10→0.85) | ✅ 通过 | 状态注入验证，各级累加正确（注：因 Bug #6 无法自然累积） |
| 9 | Path streak reset | ⚠️ 受 Bug #6 影响 | 切换路径时 reset 到 0 的逻辑正确，但 streak 本身无法累积 |

##### P3：其余未测 API

| # | 测试项 | 结论 | 详情 |
|---|--------|------|------|
| 10 | `GET /api/projection` 长期推演 | ✅ 通过 | 180天推演：笔记 30→1830，基金 2000→67211，link_power 25→50 |
| 11a | `GET /api/tags` 标签云 | ✅ 通过 | 返回 nodes + edges，47个标签节点正常 |
| 11b | `GET /api/notes/by-tag` 按标签查笔记 | ✅ 通过 | tag=测试 → 返回 3 条相关笔记 |
| 12 | `GET /api/income/history` 星点记录 | ✅ 通过 | 12 条记录，来源/金额/详情完整 |
| 13a | `POST /api/backup` 创建备份 | ✅ 通过 | 备份成功创建到 ~/Documents/hunterhunter_backups/ |
| 13b | `GET /api/backup/list` 备份列表 | ✅ 通过 | 返回 10 个备份，含文件数和大小 |
| 14 | `GET /api/report/monthly/draft` | ✅ 通过 | 无草稿时返回空列表 `[]`（正常） |
| 15 | `POST /api/medals/check` 手动勋章检查 | ✅ 通过 | checked:4, newly_earned:[]（全部已获得） |

##### P4：周期重置逻辑

| # | 测试项 | 结论 | 详情 |
|---|--------|------|------|
| 16 | `weekly_review_done` 新周重置 | ✅ 通过 | 设守卫=True + last_weekly_review=上周 → reset_daily_flags → False |
| 17 | `monthly_report_done` 新月重置 | ✅ 通过 | 设守卫=True + last_monthly_report=3月 → reset_daily_flags → False |
| 18 | `today_count` 跨天重置 | ✅ 通过 | 设 today_count=5 + last_capture_date=昨天 → reset_daily_flags → 0，同时 gray_medal 惩罚触发 |

##### 第四轮总结

| 类别 | ✅ 通过 | ❌ Bug | ⚠️ 受影响 |
|------|--------|--------|-----------|
| P0 核心功能 | 4 | 1 | 0 |
| P1 勋章完整性 | 3 | 0 | 0 |
| P2 路径边界 | 2 | 0 | 1 |
| P3 其余 API | 7 | 0 | 0 |
| P4 周期重置 | 3 | 0 | 0 |
| **合计** | **19** | **1** | **1** |

**新发现 Bug：**
6. **path_streak_weeks 永远不会自然累积** — `_update_path_streak()` 第 59 行 `last_choice == path` 比较类型错误：`last_choice` 存的是周字符串（"2026-21"），`path` 是路径名（"fund"/"coupon"），两者永远不等。应改为 `self.state.get("exchange_path") == path`。这意味着所有路径连续奖励/惩罚（基金+0.05~0.15、消费-0.05~-0.15）**对真实用户完全不可达**，只能通过手动修改 state.json 触发。

**累计 Bug 清单（四轮合计）：**

| # | Bug | 严重度 | 位置 | 状态 |
|---|-----|--------|------|:----:|
| 1 | 重复检测是位置匹配而非文本相似度 | 中 | `engine_capture.py:_check_duplicate` | ⏳ 暂缓 |
| 2 | 跨界采集加成从未上线 | 低 | `engine_capture.py:_calculate_stars` | ⏳ 暂缓 |
| 3 | 周回顾可重复提交 | 高 | `engine_review.py:submit_weekly_review` | ✅ 已修复 |
| 4 | 消费路径连续惩罚从未生效 | 中 | `engine_exchange.py:_calculate_exchange_rate` | ✅ 已修复 |
| 5 | 月度战报可重复提交 | 高 | `engine_review.py:submit_monthly_report` | ✅ 已修复 |
| 6 | path_streak_weeks 永远不累积 | 高 | `engine_exchange.py:_update_path_streak:59` | ❌ 待修复 |

---

## 五、配置化优先级建议

| 优先级 | 配置项 | 理由 |
|--------|--------|------|
| **P0** | `ENABLE_SEASON` | 赛季已下线，需要明确开关控制 |
| **P1** | `DUPLICATE_THRESHOLD` | 相似度阈值应可调整，便于测试 |
| **P2** | `DUPLICATE_CHECK_ENABLED` | 重复检测可独立开关，便于调试 |
| **P3** | `STREAK_BONUS_ENABLED` | 连续加成可独立开关 |
| **P4** | `CROSS_DOMAIN_BONUS_ENABLED` | 跨界加成可独立开关 |

---

## 六、规则依赖关系

```
采集模块
├── 重复检测 (_check_duplicate)
├── 每日倍率 (daily_multipliers)
├── 连续加成 (streak_bonuses)
└── 跨界加成 (cross_domain_bonus)

兑换模块
├── 模块开关 (ENABLE_EXCHANGE)
├── 基金规则 (fund.min_withdraw, fund.base_rate)
├── 消费规则 (coupon_rate)
└── 路径奖励 (path_bonuses)

赛季模块
├── 模块开关 (ENABLE_SEASON)
├── 赛季长度 (seasons.default_length_days)
└── 星点上限 (season_star_cap)

回顾模块
├── 周回顾奖励 (weekly_review_reward)
└── 月度战报奖励 (monthly_report_reward)
```

---

## 更新记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-05-25 | v0.4.1-dev | 初始版本 + 第一轮测试（真实数据） |
| 2026-05-25 | v0.4.1-dev | 第二轮测试（虚拟历史数据）：补充连续加成/兑换门槛/路径奖励/回顾/ENABLE_EXCHANGE 测试，发现周回顾重复提交 Bug |
| 2026-05-25 | v0.4.1-dev | 第三轮测试（补测清单外在线项）：消费路径/30天+90天连续加成/月度战报重复提交/勋章+连接力 |
| 2026-05-25 | v0.4.1-dev | Bug 修复：#3 周回顾守卫、#4 消费路径惩罚、#5 月度战报守卫 |
| 2026-05-25 | v0.4.1-dev | 第四轮测试（API全覆盖+勋章+路径边界+周期重置）：18项通过，发现 Bug #6 path_streak_weeks 永不可累积 |