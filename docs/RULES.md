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
| 2026-05-25 | v0.4.1-dev | 初始版本 |