import json
import os
import re
import yaml
import math
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock

class HuntingEngine:
    def __init__(self, base_path=None):
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = Path(__file__).parent / "data" / "inspire"
        
        self.system_folder = self.base_path / "_狩猎系统"
        self.state_file = self.system_folder / "state.json"
        self.config_file = self.system_folder / "config.yaml"
        self.inbox_folder = self.base_path / "Inbox"
        self.exchange_log_file = self.system_folder / "exchange_log.md"
        self.system_log_file = self.system_folder / "system_log.md"
        
        self.lock = Lock()
        
        # 初始化日志系统
        self._init_logging()
        
        self._init_system()
        self._load_config()
        self._load_state()
        self._migrate_state_v022()
        
        self._log_event("SYSTEM_START", "狩猎系统启动")
    
    def _init_logging(self):
        """初始化日志系统"""
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(self.system_log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("HuntingEngine")
    
    def _log_event(self, event_type, message, details=None):
        """记录系统事件日志"""
        timestamp = datetime.now().isoformat()
        log_entry = f"## {timestamp} [{event_type}]\n"
        log_entry += f"- 消息：{message}\n"
        
        if details:
            if isinstance(details, dict):
                for key, value in details.items():
                    log_entry += f"- {key}: {value}\n"
            else:
                log_entry += f"- 详情：{details}\n"
        
        log_entry += "\n"
        
        # 写入日志文件
        with open(self.system_log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        # 同时输出到控制台
        self.logger.info(f"[{event_type}] {message}" + (f" | {details}" if details else ""))
    
    def _init_system(self):
        self.system_folder.mkdir(parents=True, exist_ok=True)
        self.inbox_folder.mkdir(parents=True, exist_ok=True)
        
        if not self.config_file.exists():
            self._write_default_config()
        
        if not self.state_file.exists():
            self._write_default_state()
        
        if not self.exchange_log_file.exists():
            with open(self.exchange_log_file, 'w', encoding='utf-8') as f:
                f.write("# 兑换记录\n\n")
    
    def _write_default_config(self):
        default_config = {
            "base_star": 10,
            "daily_multipliers": [1.0, 1.5, 2.0, 0.2],
            "weekly_review_reward": 200,
            "monthly_report_reward": 500,
            "content_output_reward_min": 750,
            "content_output_reward_max": 1000,
            "content_output_max_times": 5,
            "coupon_rate": 1.0,
            "custom_fund_name": "我的投资账户",
            
            # 连续加成配置
            "streak_bonuses": [
                {"days": 7, "bonus_pct": 10},
                {"days": 30, "bonus_pct": 30},
                {"days": 90, "bonus_pct": 50}
            ],
            
            # 基金配置
            "fund": {
                "base_rate": 1.5,
                "lock_days": 30,
                "min_withdraw": 500
            },
            
            # 连续选择奖惩
            "path_bonuses": {
                "fund": [
                    {"weeks": 2, "rate": 1.55},
                    {"weeks": 4, "rate": 1.60},
                    {"weeks": 8, "rate": 1.65}
                ],
                "coupon": [
                    {"weeks": 2, "rate": 0.95},
                    {"weeks": 4, "rate": 0.90},
                    {"weeks": 8, "rate": 0.85}
                ]
            },
            
            # 连接力星点奖励 (v0.24)
            "link_power_rewards": [
                {"threshold": 5, "reward": 50},
                {"threshold": 20, "reward": 100},
                {"threshold": 50, "reward": 200}
            ],
            
            # 跨界采集加成 (v0.24)
            "cross_domain_bonus": 5,
            
            # 赛季星点限制 (v0.24)
            "season_star_cap": 3000,
            "season_soft_reset_ratio": 0.5,
            
            # 赛季配置 (v0.24)
            "seasons": {
                "default_length_days": 15,
                "auto_start": True
            }
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
    
    def _write_default_state(self):
        today = datetime.now().strftime("%Y-%m-%d")
        default_state = {
            "total_star": 0.0,
            "today_count": 0,
            "last_capture_date": "",
            "streak_days": 0,
            "active_days": 0,
            "total_notes": 0,
            
            # 惩罚机制（保留字段兼容旧数据）
            "penalty_active": False,
            "penalty_days": 0,
            
            "medals": [],
            "monthly_medals": 0,
            "gray_medal": False,
            "last_weekly_review": "",
            "last_monthly_report": "",
            "weekly_review_done": False,
            "monthly_report_done": False,
            "completed_reports": 0,
            "exchange_history": [],
            
            # 兑换系统
            "exchange_path": "",
            "fund_pool": 0.0,
            "fund_first_opened_at": None,  # 基金首次开通日期，用于30天锁定期校验
            "available_star": 0.0,
            "consumption_loss_this_month": 0.0,
            "path_streak_weeks": 0,
            "last_path_choice": "",
            
            # 内容输出
            "published_count": 0,
            "total_output_star": 0,
            
            # 能力值系统（v0.23：仅保留连接力，采集力/输出力已废除）
            "abilities": {
                "link_power": 0.0
            },
            "link_power_rewards_earned": [],  # 本季已触发的连接力奖励阈值
            
            # 标签共现图
            "cross_domain_notes_count": 0,
            "tag_graph": {
                "nodes": {},
                "edges": {}
            },
            
            # 赛季系统
            "current_season": {
                "id": 1,
                "name": "开拓者",
                "start_date": today,
                "end_date": "",
                "theme_tags": [],
                "star_earned_this_season": 0,
                "cross_domain_notes_this_season": 0,
                "active_days_this_season": 0
            },
            "season_history": []
        }
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(default_state, f, ensure_ascii=False, indent=2)
    
    def _migrate_state_v022(self):
        """将旧版 state.json 迁移到 v0.22 新结构"""
        needs_migration = False
        
        # 检查是否需要迁移（缺少新字段）
        required_fields = [
            "active_days", "total_notes", "fund_pool", "available_star",
            "consumption_loss_this_month", "path_streak_weeks", "last_path_choice",
            "total_output_star", "abilities", "ability_changes",
            "cross_domain_notes_count", "tag_graph", "current_season", "season_history",
            "completed_reports"
        ]
        
        for field in required_fields:
            if field not in self.state:
                needs_migration = True
                break
        
        if not needs_migration:
            return
        
        # 备份旧状态
        backup_path = self.system_folder / "state.json.backup.v01"
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
        
        # 保留原有字段
        old_total_star = self.state.get("total_star", 0.0)
        
        # 初始化新增字段
        self.state.setdefault("active_days", 0)
        self.state.setdefault("total_notes", 0)
        
        # 兑换系统
        self.state.setdefault("exchange_path", "")
        self.state.setdefault("fund_pool", 0.0)
        self.state.setdefault("fund_first_opened_at", None)  # 基金首次开通日期
        self.state.setdefault("available_star", old_total_star)  # 初始时可用星点 = 总星点
        self.state.setdefault("consumption_loss_this_month", 0.0)
        self.state.setdefault("path_streak_weeks", 0)
        self.state.setdefault("last_path_choice", "")
        
        # 内容输出
        self.state.setdefault("total_output_star", 0)
        
        # 能力值系统（v0.23：仅保留连接力）
        self.state.setdefault("abilities", {
            "link_power": 0.0
        })
        self.state.setdefault("link_power_rewards_earned", [])
        
        # 标签共现图
        self.state.setdefault("cross_domain_notes_count", 0)
        self.state.setdefault("tag_graph", {
            "nodes": {},
            "edges": {}
        })
        
        # 赛季系统
        self.state.setdefault("completed_reports", 0)
        today = datetime.now().strftime("%Y-%m-%d")
        self.state.setdefault("current_season", {
            "id": 1,
            "name": "开拓者",
            "start_date": today,
            "end_date": "",
            "theme_tags": [],
            "star_earned_this_season": 0,
            "cross_domain_notes_this_season": 0,
            "active_days_this_season": 0
        })
        self.state.setdefault("season_history", [])
        
        # 初始化 tag_graph（扫描现有笔记）
        self._init_tag_graph_from_notes()
        
        # 计算初始能力值
        self._calculate_link_power()
        
        self._save_state()
    
    def _init_tag_graph_from_notes(self):
        """从现有笔记初始化 tag_graph"""
        if self.state["tag_graph"]["nodes"] and self.state["tag_graph"]["edges"]:
            return
        
        nodes = {}
        edges = {}
        total_notes = 0
        cross_domain_count = 0
        
        for file in self.inbox_folder.glob("灵感-*.md"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if not content.startswith('---'):
                    continue
                
                parts = content.split('---', 2)
                if len(parts) < 3:
                    continue
                
                frontmatter_text = parts[1]
                if 'hunt: true' not in frontmatter_text and 'hunt: True' not in frontmatter_text:
                    continue
                
                tags_match = re.search(r'tags:\s*\[(.+?)\]', frontmatter_text)
                if not tags_match:
                    continue
                
                tag_list = tags_match.group(1)
                tags = [t.strip().strip("'\"") for t in tag_list.split(',')]
                tags = tags[:5]  # 只取前5个
                
                total_notes += 1
                
                # 更新节点
                for tag in tags:
                    if tag not in nodes:
                        nodes[tag] = {"count": 0, "first_seen": self._get_today_str()}
                    nodes[tag]["count"] += 1
                
                # 更新边（两两配对）
                for i in range(len(tags)):
                    for j in range(i + 1, len(tags)):
                        edge_key = f"{tags[i]}<->{tags[j]}"
                        edges[edge_key] = edges.get(edge_key, 0) + 1
                
                # 检测跨界笔记
                domains = set()
                for tag in tags:
                    domain = tag.split('/')[0] if '/' in tag else tag
                    domains.add(domain)
                if len(domains) >= 2:
                    cross_domain_count += 1
            
            except Exception:
                continue
        
        self.state["tag_graph"]["nodes"] = nodes
        self.state["tag_graph"]["edges"] = edges
        self.state["total_notes"] = total_notes
        self.state["cross_domain_notes_count"] = cross_domain_count
    
    def _calculate_link_power(self):
        """计算连接力"""
        nodes = self.state["tag_graph"]["nodes"]
        edges = self.state["tag_graph"]["edges"]
        cross_domain_count = self.state["cross_domain_notes_count"]
        total_notes = self.state["total_notes"]
        
        nodes_count = len(nodes)
        edges_count = sum(edges.values())
        
        if nodes_count < 2:
            link_power = 0.1
        else:
            max_edges = nodes_count * (nodes_count - 1) / 2
            density = edges_count / max_edges
            cross_domain_ratio = cross_domain_count / max(total_notes, 1)
            link_power = density * 100 * math.log2(nodes_count + 1) * (cross_domain_ratio + 0.1)
        
        # 限制范围 0.1~50
        link_power = max(0.1, min(50.0, link_power))
        
        self.state["abilities"]["link_power"] = link_power
    
    def _check_link_power_rewards(self):
        """检查连接力阈值星点奖励（每赛季每个阈值只触发一次）"""
        link_power = self.state["abilities"]["link_power"]
        earned = self.state.setdefault("link_power_rewards_earned", [])
        rewards_config = self.config.get("link_power_rewards", [])
        
        newly_earned_rewards = []
        for reward_item in rewards_config:
            threshold = reward_item["threshold"]
            if link_power >= threshold and threshold not in earned:
                star_reward = reward_item["reward"]
                self.state["available_star"] += star_reward
                self.state["total_star"] = self.state["available_star"] + self.state["fund_pool"]
                earned.append(threshold)
                newly_earned_rewards.append({
                    "threshold": threshold,
                    "reward": star_reward
                })
                self._log_event("LINK_POWER_REWARD", f"连接力达到 {threshold}，获得 {star_reward} 星点")
        
        return newly_earned_rewards
    
    def _load_config(self):
        with open(self.config_file, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 确保 fund_base_rate 字段存在（兼容配置结构）
        if 'fund' in self.config and 'base_rate' in self.config['fund']:
            self.config['fund_base_rate'] = self.config['fund']['base_rate']
    
    def _load_state(self):
        with open(self.state_file, 'r', encoding='utf-8') as f:
            self.state = json.load(f)
    
    def _save_state(self):
        with self.lock:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
    
    def _save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
    
    def _get_today_str(self):
        return datetime.now().strftime("%Y-%m-%d")
    
    def _get_week_str(self):
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        return start_of_week.strftime("%Y-%W")
    
    def _get_month_str(self):
        return datetime.now().strftime("%Y-%m")
    
    def _check_streak(self):
        today = self._get_today_str()
        last_date = self.state["last_capture_date"]
        
        if not last_date:
            self.state["streak_days"] = 1
            self.state["last_capture_date"] = today
            self.state["active_days"] += 1
            return
        
        last_dt = datetime.strptime(last_date, "%Y-%m-%d")
        today_dt = datetime.strptime(today, "%Y-%m-%d")
        diff_days = (today_dt - last_dt).days
        
        if diff_days == 1:
            self.state["streak_days"] += 1
            self.state["active_days"] += 1
        elif diff_days > 1:
            self.state["streak_days"] = 1
            self.state["active_days"] += 1
        
        self.state["last_capture_date"] = today
    
    def _calculate_stars(self):
        """计算本次采集获得的星点（包含连续加成）"""
        count = self.state["today_count"]
        multipliers = self.config.get("daily_multipliers", [1.0, 1.5, 2.0, 0.2])
        
        if count <= len(multipliers):
            multiplier = multipliers[count - 1]
        else:
            multiplier = multipliers[-1]
        
        base = self.config.get("base_star", 10)
        stars = base * multiplier
        
        # 连续加成（只对第1条采集生效）
        if count == 1:
            streak_bonuses = self.config.get("streak_bonuses", [])
            streak_days = self.state["streak_days"]
            
            for bonus in reversed(streak_bonuses):
                if streak_days >= bonus["days"]:
                    stars *= (1 + bonus["bonus_pct"] / 100)
                    break
        
        return stars
    
    def _check_medals(self, trigger_type=None):
        """检查并发放勋章（从 config.yaml 读取配置表）"""
        medals_config = self.config.get("medals", [])
        newly_earned = []
        
        for medal in medals_config:
            medal_id = medal["id"]
            medal_name = medal["name"]
            
            # 检查是否已获得
            if medal_name in self.state["medals"]:
                continue
            
            # 检查是否有触发类型筛选
            if trigger_type and medal.get("trigger") != trigger_type:
                continue
            
            # 根据触发类型检查条件
            earned = False
            
            if medal["trigger"] == "event":
                earned = self._check_event_medal(medal)
            elif medal["trigger"] == "ability":
                earned = self._check_ability_medal(medal)
            elif medal["trigger"] == "season":
                earned = self._check_season_medal(medal)
            
            if earned:
                self.state["medals"].append(medal_name)
                newly_earned.append(medal)
        
        return newly_earned
    
    def _check_event_medal(self, medal):
        """检查事件触发类型勋章"""
        event_type = medal.get("event")
        condition = medal.get("condition", "")
        
        if event_type == "daily_capture_count":
            today_count = self.state["today_count"]
            match = re.search(r'count\s*>=?\s*(\d+)', condition)
            if match:
                threshold = int(match.group(1))
                return today_count >= threshold
        
        elif event_type == "weekly_review_streak":
            streak = self.state.get("weekly_review_streak", 0)
            match = re.search(r'streak\s*>=?\s*(\d+)', condition)
            if match:
                threshold = int(match.group(1))
                return streak >= threshold
        
        elif event_type == "monthly_report_cross_domain":
            last_report_tag_count = self.state.get("_last_report_tag_count", 0)
            match = re.search(r'count\s*>=?\s*(\d+)', condition)
            if match:
                threshold = int(match.group(1))
                return last_report_tag_count >= threshold
        
        return False
    
    def _check_ability_medal(self, medal):
        """检查能力值触发类型勋章"""
        ability_type = medal.get("ability")
        threshold = medal.get("threshold", 0)
        
        if ability_type in self.state["abilities"]:
            current_value = self.state["abilities"][ability_type]
            return current_value >= threshold
        
        return False
    
    def _check_season_medal(self, medal):
        """检查赛季触发类型勋章"""
        season_theme = medal.get("season_theme")
        current_season = self.state.get("current_season", {})
        
        if current_season.get("name") == season_theme:
            # 在赛季结算时发放
            return False
        
        return False
    
    def get_all_medals(self):
        """获取所有勋章定义和状态"""
        medals_config = self.config.get("medals", [])
        result = []
        
        for medal in medals_config:
            medal_name = medal["name"]
            earned = medal_name in self.state["medals"]
            
            # 获取获得日期（简单实现）
            earned_at = None
            
            result.append({
                "id": medal["id"],
                "name": medal_name,
                "icon": medal.get("icon", "🏅"),
                "trigger": medal.get("trigger"),
                "condition": self._get_medal_condition_desc(medal),
                "earned": earned,
                "earned_at": earned_at
            })
        
        return result
    
    def _get_medal_condition_desc(self, medal):
        """生成勋章条件描述"""
        trigger = medal.get("trigger")
        
        if trigger == "event":
            event_type = medal.get("event")
            if event_type == "daily_capture_count":
                return "单日完成3条采集"
            elif event_type == "weekly_review_streak":
                return "连续4周完成周回顾"
            elif event_type == "monthly_report_cross_domain":
                return "单篇战报连接3个领域"
            return f"事件: {event_type}"
        
        elif trigger == "ability":
            ability_map = {
                "link_power": "连接力"
            }
            ability_name = ability_map.get(medal["ability"], medal["ability"])
            return f"{ability_name} ≥ {medal.get('threshold')}"
        
        elif trigger == "season":
            return f"完成「{medal.get('season_theme')}」赛季"
        
        return ""
    
    def get_medal_status(self, medal_id):
        """获取指定勋章状态"""
        medals_config = self.config.get("medals", [])
        
        for medal in medals_config:
            if medal["id"] == medal_id:
                earned = medal["name"] in self.state["medals"]
                return {
                    "earned": earned,
                    "earned_at": None  # 简化实现
                }
        
        return {"error": "勋章不存在"}
    
    def _log_exchange(self, type_, amount, real_value):
        with open(self.exchange_log_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"- {timestamp} | {type_} | 扣除星点: {amount} | 实际价值: {real_value}\n")
    
    def _update_tag_graph(self, tags):
        """灵感提交时更新标签共现图"""
        tags = tags[:5]  # 只取前5个
        
        for tag in tags:
            if tag not in self.state["tag_graph"]["nodes"]:
                self.state["tag_graph"]["nodes"][tag] = {
                    "count": 0,
                    "first_seen": self._get_today_str()
                }
            self.state["tag_graph"]["nodes"][tag]["count"] += 1
        
        for i in range(len(tags)):
            for j in range(i + 1, len(tags)):
                edge_key = f"{tags[i]}<->{tags[j]}"
                self.state["tag_graph"]["edges"][edge_key] = self.state["tag_graph"]["edges"].get(edge_key, 0) + 1
        
        domains = set()
        for tag in tags:
            domain = tag.split('/')[0] if '/' in tag else tag
            domains.add(domain)
        
        if len(domains) >= 2:
            self.state["cross_domain_notes_count"] += 1
    
    def _calculate_exchange_rate(self, path):
        """计算当前汇率（含连续选择奖惩）"""
        path_bonuses = self.config.get("path_bonuses", {}).get(path, [])
        streak_weeks = self.state["path_streak_weeks"]
        
        if path == "fund":
            base_rate = self.config["fund"]["base_rate"]
        else:
            base_rate = self.config["coupon_rate"]
        
        rate = base_rate
        
        for bonus in path_bonuses:
            if streak_weeks >= bonus["weeks"]:
                rate = bonus["rate"]
        
        return rate
    
    def _update_path_streak(self, path):
        """更新路径连续选择计数"""
        last_choice = self.state.get("last_path_choice", "")
        last_week = self._get_week_str()
        
        if last_choice == path:
            self.state["path_streak_weeks"] += 1
        else:
            self.state["path_streak_weeks"] = 0
        
        self.state["exchange_path"] = path
        self.state["last_path_choice"] = last_week
    
    def calculate_opportunity_cost(self, amount, from_path):
        """计算镜像对比数据"""
        fund_rate = self._calculate_exchange_rate("fund")
        coupon_rate = self._calculate_exchange_rate("coupon")
        
        if from_path == "coupon":
            fund_value = amount * fund_rate
            coupon_value = amount * coupon_rate
            monthly_loss = self.state["consumption_loss_this_month"]
            monthly_gain = 0
        else:
            fund_value = amount * fund_rate
            coupon_value = amount * coupon_rate
            monthly_gain = fund_value - coupon_value
            monthly_loss = 0
        
        return {
            "fund_value": round(fund_value, 2),
            "coupon_value": round(coupon_value, 2),
            "difference": round(fund_value - coupon_value, 2),
            "monthly_loss": round(monthly_loss, 2),
            "monthly_gain": round(monthly_gain, 2)
        }
    
    def process_daily_capture(self, content, tags=None, folder="Inbox"):
        tags = tags or []
        
        # PRD 1.1：必须添加至少一个标签
        if not tags or len(tags) == 0:
            return {"error": "必须添加至少一个标签，标签由 AI 生成、你粘贴即可"}
        
        today = self._get_today_str()
        
        self._load_state()
        self._load_config()
        
        if self.state["last_capture_date"] != today:
            self.state["today_count"] = 0
            self._check_streak()
        
        self.state["today_count"] += 1
        
        # 记录采集事件
        self._log_event("CAPTURE", "灵感采集", {
            "今日次数": self.state["today_count"],
            "连续天数": self.state["streak_days"],
            "标签数量": len(tags),
            "标签": ", ".join(tags)
        })
        
        # 计算基础星星和加成
        base_stars = self.config.get("capture_base_stars", 10)
        streak_bonus_pct = 0
        streak_bonuses = self.config.get("streak_bonuses", [])
        for bonus in reversed(streak_bonuses):
            if self.state["streak_days"] >= bonus["days"]:
                streak_bonus_pct = bonus["bonus_pct"]
                break
        
        streak_bonus_amount = base_stars * streak_bonus_pct / 100
        total_stars = base_stars + streak_bonus_amount
        
        self.state["available_star"] += total_stars
        self.state["total_star"] = self.state["available_star"] + self.state["fund_pool"]
        
        date_str = datetime.now().strftime("%Y%m%d")
        time_str = datetime.now().strftime("%H%M%S")
        
        title = content.strip().split('\n')[0][:20] if content.strip() else "无标题"
        title = ''.join(c for c in title if c not in '/\\:*?"<>|# ')
        
        filename = f"灵感-{date_str}-{title}-{time_str}.md"
        
        folder_path = self.base_path / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        
        frontmatter = {
            "date": datetime.now().isoformat(),
            "tags": tags,
            "hunt": True
        }
        
        frontmatter_lines = ["---"]
        for key, value in frontmatter.items():
            if isinstance(value, list):
                frontmatter_lines.append(f"{key}: {value}")
            else:
                frontmatter_lines.append(f"{key}: {value}")
        frontmatter_lines.append("---")
        
        content = "\n".join(frontmatter_lines) + "\n\n" + content
        
        with open(folder_path / filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 记录添加标签前的边数用于检测新连接
        old_edges_count = sum(self.state["tag_graph"]["edges"].values())
        
        self._update_tag_graph(tags)
        
        # 检测新产生的标签连接
        new_edges_count = sum(self.state["tag_graph"]["edges"].values())
        new_connections = self._find_new_connections(tags) if (new_edges_count > old_edges_count) else []
        
        self.state["total_notes"] += 1
        
        self._calculate_link_power()
        link_power_rewards = self._check_link_power_rewards()
        self._check_medals()
        self._save_state()
        
        # 查找相似笔记
        related_notes = self._find_related_notes(tags, limit=3)
        
        return {
            "earned": round(total_stars, 2),
            "base_stars": round(base_stars, 2),
            "streak_bonus_pct": streak_bonus_pct,
            "streak_bonus_amount": round(streak_bonus_amount, 2),
            "total_star": round(self.state["total_star"], 2),
            "available_star": round(self.state["available_star"], 2),
            "today_count": self.state["today_count"],
            "streak_days": self.state["streak_days"],
            "link_power_rewards": link_power_rewards,
            "new_connections": new_connections,
            "related_notes": related_notes,
            "message": "捕获成功！"
        }
    
    def _find_new_connections(self, tags):
        """找出本次采集产生的新标签连接"""
        new_connections = []
        valid_tags = [t.strip('#') for t in tags if t.strip()]
        
        for i, tag1 in enumerate(valid_tags):
            for j, tag2 in enumerate(valid_tags):
                if i < j:
                    edge_key = tuple(sorted([tag1, tag2]))
                    edge_str = f"#{tag1}<->#{tag2}"
                    new_connections.append(edge_str)
        
        return new_connections
    
    def _find_related_notes(self, tags, limit=3):
        """查找相似笔记（基于标签重叠）"""
        related_notes = []
        inbox_folder = self.base_path / "Inbox"
        
        if not inbox_folder.exists():
            return related_notes
        
        tag_set = set([t.strip('#').lower() for t in tags if t.strip()])
        
        for note_file in inbox_folder.glob("*.md"):
            try:
                with open(note_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if content.startswith("---"):
                    end = content.find("\n---\n", 4)
                    if end != -1:
                        frontmatter = content[4:end]
                        lines = frontmatter.split('\n')
                        note_tags = []
                        for line in lines:
                            if line.startswith("tags:"):
                                tag_part = line[5:].strip()
                                if tag_part.startswith('[') and tag_part.endswith(']'):
                                    import ast
                                    try:
                                        note_tags = ast.literal_eval(tag_part)
                                    except:
                                        pass
                                break
                        
                        note_tag_set = set([t.strip('#').lower() for t in note_tags if t.strip()])
                        overlap = len(tag_set & note_tag_set)
                        
                        if overlap > 0:
                            title = content[end+4:].strip().split('\n')[0][:30]
                            if not title:
                                title = note_file.stem.replace("灵感-", "").split("-")[-1]
                            
                            related_notes.append({
                                "title": title,
                                "date": note_file.stem.split("-")[1],
                                "file_path": str(note_file),
                                "tag_overlap": overlap
                            })
            except:
                continue
        
        related_notes.sort(key=lambda x: x["tag_overlap"], reverse=True)
        return related_notes[:limit]
    
    def calculate_long_term_projection(self, days=180):
        """长期推演计算，基于当前速度预测未来状态"""
        self._load_state()
        
        # 计算日均采集率（基于最近30天）
        total_notes = self.state["total_notes"]
        active_days = self.state["active_days"]
        
        if active_days > 0:
            daily_note_rate = total_notes / active_days
        else:
            daily_note_rate = 1.0
        
        # 计算日均连接率
        edges_count = sum(self.state["tag_graph"]["edges"].values())
        if total_notes > 1:
            avg_connections_per_note = edges_count / (total_notes - 1)
        else:
            avg_connections_per_note = 0.5
        
        # 计算周均星点增长率
        current_fund = self.state["fund_pool"]
        current_available = self.state["available_star"]
        weekly_rate = (current_fund + current_available) / max(active_days / 7, 1)
        
        # 预测
        projected_notes = int(total_notes + daily_note_rate * days)
        projected_connections = int(edges_count + avg_connections_per_note * daily_note_rate * days)
        projected_fund = round(current_fund + weekly_rate * (days / 7), 2)
        
        # 连接力预测
        current_abilities = self.state["abilities"]
        projected_abilities = {}
        
        for ability, value in current_abilities.items():
            if ability == "link_power":
                projected = min(50, value + (projected_connections - edges_count) * 0.05)
            else:
                projected = value
            projected_abilities[ability] = round(projected, 2)
        
        # 赛季进度
        season_start = self.state["current_season"].get("start_date")
        if season_start:
            season_start_date = datetime.strptime(season_start, "%Y-%m-%d")
            today = datetime.now().date()
            season_days = (today - season_start_date.date()).days
            total_season_days = 90
        else:
            season_days = 0
            total_season_days = 90
        
        return {
            "projection_days": days,
            "notes_projection": {
                "current": total_notes,
                "projected": projected_notes,
                "daily_rate": round(daily_note_rate, 2)
            },
            "connections_projection": {
                "current": edges_count,
                "projected": projected_connections,
                "daily_rate": round(avg_connections_per_note * daily_note_rate, 2)
            },
            "fund_projection": {
                "current": round(current_fund, 2),
                "projected": projected_fund,
                "weekly_rate": round(weekly_rate, 2)
            },
            "abilities_projection": {
                ability: {
                    "current": round(current_abilities[ability], 2),
                    "projected": projected_abilities[ability]
                }
                for ability in current_abilities
            },
            "season_progress": {
                "current_season_days": season_days,
                "total_season_days": total_season_days,
                "completion_pct": round((season_days / total_season_days) * 100, 2)
            }
        }
    
    def get_status(self):
        self._load_state()
        
        # 计算连续加成百分比
        streak_bonus_pct = 0
        streak_bonuses = self.config.get("streak_bonuses", [])
        streak_days = self.state["streak_days"]
        for bonus in reversed(streak_bonuses):
            if streak_days >= bonus["days"]:
                streak_bonus_pct = bonus["bonus_pct"]
                break
        
        return {
            "total_star": round(self.state["total_star"], 2),
            "available_star": round(self.state["available_star"], 2),
            "fund_pool": round(self.state["fund_pool"], 2),
            "today_count": self.state["today_count"],
            "streak_days": self.state["streak_days"],
            "streak_bonus_pct": streak_bonus_pct,
            "medals": self.state["medals"],
            "monthly_medals": self.state["monthly_medals"],
            "gray_medal": self.state["gray_medal"],
            "weekly_review_done": self.state["weekly_review_done"],
            "monthly_report_done": self.state["monthly_report_done"],
            "published_count": self.state.get("published_count", 0),
            "exchange_path": self.state["exchange_path"],
            "path_streak_weeks": self.state["path_streak_weeks"],
            "consumption_loss_this_month": round(self.state["consumption_loss_this_month"], 2),
            "current_season": self.state["current_season"],
            "total_notes": self.state["total_notes"],
            "active_days": self.state["active_days"],
            "fund_bonus": self.state.get("fund_bonus", 0)
        }
    
    def process_publish(self, url):
        self._load_state()
        self._load_config()
        
        max_times = self.config.get("content_output_max_times", 5)
        if self.state.get("published_count", 0) >= max_times:
            return {"error": f"已达到最大发布次数（{max_times}次）"}
        
        min_reward = self.config.get("content_output_reward_min", 750)
        max_reward = self.config.get("content_output_reward_max", 1000)
        
        # 检查星点里程碑阈值加成（≥2000 星点 → 输出奖励下限提升至 850）
        total_star = self.state["total_star"]
        if total_star >= 2000:
            min_reward = 850
        
        reward = int(min_reward + (max_reward - min_reward) * random.random())
        
        if "published_count" not in self.state:
            self.state["published_count"] = 0
        self.state["published_count"] += 1
        self.state["total_output_star"] += reward
        self.state["available_star"] += reward
        self.state["total_star"] = self.state["available_star"] + self.state["fund_pool"]
        
        self._calculate_link_power()
        self._save_state()
        
        return {
            "reward": reward,
            "total_star": round(self.state["total_star"], 2),
            "available_star": round(self.state["available_star"], 2),
            "published_count": self.state["published_count"],
            "message": "发布成功！"
        }
    
    def set_exchange_path(self, path):
        """选择本周兑换路径"""
        if path not in ["coupon", "fund"]:
            return {"error": "无效路径，只能选择 coupon 或 fund"}
        
        self._load_state()
        self._update_path_streak(path)
        self._save_state()
        
        rate = self._calculate_exchange_rate(path)
        
        return {
            "message": f"本周已选择{path}路径",
            "path": path,
            "rate": round(rate, 2),
            "streak_weeks": self.state["path_streak_weeks"]
        }
    
    def exchange_coupon(self, amount):
        """消费券兑换"""
        self._load_state()
        
        if self.state["available_star"] < amount:
            return {"error": "可用星点不足"}
        
        self.state["available_star"] -= amount
        self.state["total_star"] = self.state["available_star"] + self.state["fund_pool"]
        
        rate = self._calculate_exchange_rate("coupon")
        real_value = amount * rate
        
        # 更新本月消费损失
        fund_rate = self._calculate_exchange_rate("fund")
        opportunity_loss = amount * (fund_rate - rate)
        self.state["consumption_loss_this_month"] += opportunity_loss
        
        self._log_exchange("coupon", amount, real_value)
        
        self.state["exchange_history"].append({
            "type": "coupon",
            "amount": amount,
            "real_value": real_value,
            "timestamp": datetime.now().isoformat()
        })
        
        opportunity_cost = self.calculate_opportunity_cost(amount, "coupon")
        
        self._save_state()
        
        return {
            "deducted_star": amount,
            "real_value": round(real_value, 2),
            "new_balance": round(self.state["available_star"], 2),
            "opportunity_cost": opportunity_cost,
            "message": "请手动转账"
        }
    
    def exchange_fund(self, amount):
        """基金兑换"""
        self._load_state()
        
        if self.state["available_star"] < amount:
            return {"error": "可用星点不足"}
        
        # 检查基金门槛：最低额度
        min_withdraw = self.config["fund"].get("min_withdraw", 500)
        if amount < min_withdraw:
            return {"error": f"基金兑换最低额度为 {min_withdraw} 星点"}
        
        # 检查基金门槛：30天锁定期
        lock_days = self.config["fund"].get("lock_days", 30)
        first_opened = self.state.get("fund_first_opened_at")
        if first_opened:
            first_dt = datetime.strptime(first_opened, "%Y-%m-%d").date()
            days_since = (datetime.now().date() - first_dt).days
            if days_since < lock_days:
                remaining = lock_days - days_since
                return {"error": f"基金首次开通后锁定 {lock_days} 天，还需 {remaining} 天解锁"}
        
        # 记录首次开通日期
        if not first_opened:
            self.state["fund_first_opened_at"] = self._get_today_str()
        
        self.state["available_star"] -= amount
        self.state["fund_pool"] += amount
        self.state["total_star"] = self.state["available_star"] + self.state["fund_pool"]
        
        rate = self._calculate_exchange_rate("fund")
        real_value = amount * rate
        
        self._log_exchange("fund", amount, real_value)
        
        self.state["exchange_history"].append({
            "type": "fund",
            "amount": amount,
            "real_value": real_value,
            "timestamp": datetime.now().isoformat()
        })
        
        opportunity_cost = self.calculate_opportunity_cost(amount, "fund")
        
        self._save_state()
        
        return {
            "deducted_star": amount,
            "real_value": round(real_value, 2),
            "new_balance": round(self.state["fund_pool"], 2),
            "opportunity_cost": opportunity_cost,
            "message": "请手动转账"
        }
    
    # ========== 回顾与战报：两步流程 ==========

    def _get_previous_week_range(self):
        today = datetime.now().date()
        current_monday = today - timedelta(days=today.weekday())
        prev_monday = current_monday - timedelta(days=7)
        prev_sunday = prev_monday + timedelta(days=6)
        return prev_monday, prev_sunday

    def _get_previous_month_range(self):
        today = datetime.now().date()
        first_day_this_month = today.replace(day=1)
        last_day_prev_month = first_day_this_month - timedelta(days=1)
        first_day_prev_month = last_day_prev_month.replace(day=1)
        return first_day_prev_month, last_day_prev_month

    def _get_week_label(self, monday_date):
        year = monday_date.year
        week_num = monday_date.isocalendar()[1]
        return f"{year}年第{week_num}周"

    def _get_month_label(self, year, month):
        return f"{year}年{month}月"

    def _scan_notes(self, start_date, end_date):
        notes = []
        for file in sorted(self.inbox_folder.glob("灵感-*.md")):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    raw_content = f.read()

                if not raw_content.startswith('---'):
                    continue

                parts = raw_content.split('---', 2)
                if len(parts) < 3:
                    continue

                frontmatter_text = parts[1]
                body = parts[2].strip()

                if 'hunt: true' not in frontmatter_text and 'hunt: True' not in frontmatter_text:
                    continue

                date_match = re.search(r'date:\s*(.+)', frontmatter_text)
                if not date_match:
                    continue

                date_str = date_match.group(1).strip()
                try:
                    note_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
                except Exception:
                    continue

                if not (start_date <= note_date <= end_date):
                    continue

                tags = []
                tags_match = re.search(r'tags:\s*\[(.+?)\]', frontmatter_text)
                if tags_match:
                    tag_list = tags_match.group(1)
                    tags = [t.strip().strip("'\"") for t in tag_list.split(',')]

                title = file.stem
                if title.startswith('灵感-'):
                    title = title[3:]

                notes.append({
                    'date': note_date,
                    'date_str': note_date.strftime('%Y-%m-%d'),
                    'weekday': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][note_date.weekday()],
                    'tags': tags,
                    'body': body,
                    'title': title,
                    'filename': file.name
                })
            except Exception:
                continue

        notes.sort(key=lambda n: n['date'])
        return notes

    def _build_material_content(self, notes, title, date_range_label):
        # 生成数据叙事
        narrative = self._generate_data_narrative(notes, "周" if "周" in title else "月")
        
        # 找出峰值时刻
        peak_moments = self._find_peak_moments(notes)
        
        lines = [
            f"# {title}",
            "",
            f"> 时间范围：{date_range_label}",
            f"> 共 {len(notes)} 条灵感碎片",
            "",
            "## 📊 数据概览",
            "",
            narrative,
            ""
        ]
        
        if peak_moments:
            lines.append("## 🌟 峰值时刻")
            lines.append("")
            for peak in peak_moments:
                lines.append(f"- **{peak['label']}**：{peak['description']}")
            lines.append("")
        
        lines.append("## 💡 灵感碎片" if "周" in title else "## 💡 灵感碎片")
        lines.append("")

        for note in notes:
            tag_str = ' '.join(f"#{t}" for t in note['tags'])
            lines.append(f"### {note['date_str']} {note['weekday']}")
            lines.append(f"**{note['title'][:30]}**  {tag_str}")
            lines.append("")
            lines.append(note['body'])
            lines.append("")
            lines.append("---")
            lines.append("")

        return '\n'.join(lines)
    
    def _generate_data_narrative(self, notes, period_type):
        """生成一句话数据叙事"""
        if not notes:
            return "本周暂无灵感记录。"
        
        # 统计标签
        all_tags = []
        for note in notes:
            all_tags.extend(note['tags'])
        
        unique_tags = set(all_tags)
        tag_count = len(unique_tags)
        
        # 找出最常用的标签
        tag_freq = {}
        for tag in all_tags:
            tag_freq[tag] = tag_freq.get(tag, 0) + 1
        
        top_tags = sorted(tag_freq.items(), key=lambda x: x[1], reverse=True)[:3]
        top_tag_names = "、".join([f"#{t[0]}" for t in top_tags]) if top_tags else "暂无"
        
        # 计算平均每天采集数
        dates = set(n['date'] for n in notes)
        avg_per_day = len(notes) / max(len(dates), 1)
        
        # 生成叙事
        if period_type == "周":
            narratives = [
                f"本周你记录了 {len(notes)} 条灵感，分布在 {len(dates)} 天，涉及 {tag_count} 个不同领域",
                f"本周持续探索，平均每天捕获 {avg_per_day:.1f} 条灵感",
                f"本周你关注的核心领域是 {top_tag_names}",
            ]
        else:
            narratives = [
                f"本月你记录了 {len(notes)} 条灵感，横跨 {len(dates)} 天",
                f"本月你探索了 {tag_count} 个不同的知识领域",
                f"本月你最常提及的是 {top_tag_names}",
            ]
        
        return narratives[0] + "。"
    
    def _find_peak_moments(self, notes):
        """找出峰值时刻"""
        if not notes:
            return []
        
        peaks = []
        
        # 找出标签最多的笔记（最跨界）
        if notes:
            max_tags_note = max(notes, key=lambda n: len(n['tags']))
            if len(max_tags_note['tags']) >= 3:
                peaks.append({
                    "label": "最跨界灵感",
                    "description": f"「{max_tags_note['title'][:20]}」连接了 {len(max_tags_note['tags'])} 个领域"
                })
        
        # 找出内容最长的笔记（最深度）
        if notes:
            longest_note = max(notes, key=lambda n: len(n['body']))
            if len(longest_note['body']) >= 100:
                peaks.append({
                    "label": "最深度思考",
                    "description": f"「{longest_note['title'][:20]}」展开了 {len(longest_note['body'])} 字的思考"
                })
        
        # 找出跨周几的记录（最特别）
        weekdays = [n['weekday'] for n in notes]
        if '周六' in weekdays or '周日' in weekdays:
            weekend_notes = [n for n in notes if n['weekday'] in ['周六', '周日']]
            if weekend_notes:
                peaks.append({
                    "label": "周末灵感",
                    "description": f"周末也保持采集，记录了 {len(weekend_notes)} 条"
                })
        
        return peaks[:3]  # 最多返回3个峰值

    def generate_weekly_review(self):
        self._load_state()

        prev_monday, prev_sunday = self._get_previous_week_range()
        week_label = self._get_week_label(prev_monday)

        if self.state["weekly_review_done"] and self.state["last_weekly_review"]:
            return {"error": f"本周回顾已完成（{self.state['last_weekly_review']}）"}

        notes = self._scan_notes(prev_monday, prev_sunday)
        if not notes:
            return {
                "error": f"上一自然周（{prev_monday} 至 {prev_sunday}）没有灵感笔记，无法生成回顾素材"
            }

        date_range_label = f"{prev_monday.strftime('%Y-%m-%d')}（周一）至 {prev_sunday.strftime('%Y-%m-%d')}（周日）"
        content = self._build_material_content(notes, f"周回顾素材 - {week_label}", date_range_label)

        filename = f"周回顾素材-{week_label}.md"
        file_path = self.inbox_folder / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            "file_path": str(file_path),
            "filename": filename,
            "content": content,
            "week_label": week_label,
            "date_range": date_range_label,
            "note_count": len(notes)
        }

    def _extract_tags_from_content(self, content):
        tags = set()
        for match in re.finditer(r'#(\S+)', content):
            tag = match.group(1)
            if tag not in ('周回顾', '月回顾'):
                tags.add(tag)
        return sorted(tags)

    def _prepend_frontmatter(self, file_path, tags, tag_label):
        fp = Path(file_path)
        with open(fp, 'r', encoding='utf-8') as f:
            original = f.read()

        all_tags = tags + [tag_label]
        frontmatter = f"""---
date: {datetime.now().isoformat()}
tags: {all_tags}
hunt: true
---

"""
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(frontmatter + original)

    def submit_weekly_review(self, file_path, insight):
        self._load_state()

        fp = Path(file_path)
        if not fp.exists():
            return {"error": "素材文件不存在，请先点击周回顾生成素材"}

        with open(fp, 'r', encoding='utf-8') as f:
            existing = f.read()

        tags = self._extract_tags_from_content(existing)

        with open(fp, 'a', encoding='utf-8') as f:
            f.write(f"\n## 本周核心洞察\n\n{insight}\n\n")

        self._prepend_frontmatter(file_path, tags, "周回顾")

        current_week = self._get_week_str()
        self.state["last_weekly_review"] = current_week
        self.state["weekly_review_done"] = True
        self.state["available_star"] += self.config["weekly_review_reward"]
        self.state["total_star"] = self.state["available_star"] + self.state["fund_pool"]

        self._calculate_link_power()
        self._save_state()

        return {
            "reward": self.config["weekly_review_reward"],
            "new_balance": round(self.state["available_star"], 2),
            "message": "周回顾完成！"
        }

    def generate_monthly_report(self):
        self._load_state()

        prev_first, prev_last = self._get_previous_month_range()
        month_label = self._get_month_label(prev_first.year, prev_first.month)

        if self.state["monthly_report_done"] and self.state["last_monthly_report"]:
            return {"error": f"本月战报已完成（{self.state['last_monthly_report']}）"}

        notes = self._scan_notes(prev_first, prev_last)
        if not notes:
            return {
                "error": f"上一自然月（{prev_first} 至 {prev_last}）没有灵感笔记，无法生成战报素材"
            }

        date_range_label = f"{prev_first.strftime('%Y-%m-%d')} 至 {prev_last.strftime('%Y-%m-%d')}"
        content = self._build_material_content(notes, f"月度战报素材 - {month_label}", date_range_label)

        filename = f"月度战报素材-{month_label}.md"
        file_path = self.inbox_folder / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            "file_path": str(file_path),
            "filename": filename,
            "content": content,
            "month_label": month_label,
            "date_range": date_range_label,
            "note_count": len(notes)
        }

    def submit_monthly_report(self, file_path, insight):
        self._load_state()

        fp = Path(file_path)
        if not fp.exists():
            return {"error": "素材文件不存在，请先点击月度战报生成素材"}

        with open(fp, 'r', encoding='utf-8') as f:
            existing = f.read()

        tags = self._extract_tags_from_content(existing)

        with open(fp, 'a', encoding='utf-8') as f:
            f.write(f"\n## 本月核心洞察\n\n{insight}\n\n")

        self._prepend_frontmatter(file_path, tags, "月回顾")

        current_month = self._get_month_str()

        if self.state["gray_medal"]:
            self.state["gray_medal"] = False
        else:
            self.state["monthly_medals"] += 1

        # 检查月度战报跨界勋章
        tag_count = len(tags)
        if tag_count >= 3:
            # 设置临时状态用于勋章检查
            self.state["_last_report_tag_count"] = tag_count
            # 检查 event 类型勋章（月度战报跨界）
            self._check_medals(trigger_type="event")

        self.state["last_monthly_report"] = current_month
        self.state["monthly_report_done"] = True
        self.state["completed_reports"] += 1
        self.state["available_star"] += self.config["monthly_report_reward"]
        self.state["total_star"] = self.state["available_star"] + self.state["fund_pool"]

        self._calculate_link_power()
        self._save_state()

        return {
            "reward": self.config["monthly_report_reward"],
            "new_balance": round(self.state["available_star"], 2),
            "monthly_medals": self.state["monthly_medals"],
            "message": "月度战报完成！"
        }

    def get_monthly_draft(self):
        current_month = self._get_month_str()
        month_dt = datetime.strptime(current_month, "%Y-%m")
        
        notes = []
        
        for file in self.inbox_folder.glob("灵感-*.md"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'hunt: true' in content:
                        lines = content.split('\n')
                        in_frontmatter = False
                        date = ""
                        tags = []
                        title = file.stem.replace("灵感-", "")
                        
                        for line in lines:
                            if line.startswith('---'):
                                in_frontmatter = not in_frontmatter
                            elif in_frontmatter:
                                if line.startswith('date:'):
                                    date = line.split(':')[1].strip()
                                elif line.startswith('tags:'):
                                    tag_content = line.split(':', 1)[1].strip()
                                    if tag_content.startswith('[') and tag_content.endswith(']'):
                                        tags = eval(tag_content)
                        
                        try:
                            file_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                            if file_date.year == month_dt.year and file_date.month == month_dt.month:
                                notes.append({
                                    "title": title,
                                    "tags": tags,
                                    "date": date
                                })
                        except:
                            continue
            except:
                continue
        
        return notes
    
    def get_config(self):
        return self.config
    
    def update_config(self, updates):
        self.config.update(updates)
        self._save_config()
        return self.config
    
    def get_tag_cloud_data(self):
        """返回标签云数据"""
        self._load_state()
        return {
            "nodes": self.state["tag_graph"]["nodes"],
            "edges": self.state["tag_graph"]["edges"]
        }
    
    def get_notes_by_tag(self, tag):
        """按标签查询笔记"""
        notes = []
        
        for file in self.inbox_folder.glob("灵感-*.md"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if not content.startswith('---'):
                    continue
                
                parts = content.split('---', 2)
                if len(parts) < 3:
                    continue
                
                frontmatter_text = parts[1]
                if 'hunt: true' not in frontmatter_text and 'hunt: True' not in frontmatter_text:
                    continue
                
                tags_match = re.search(r'tags:\s*\[(.+?)\]', frontmatter_text)
                if not tags_match:
                    continue
                
                tag_list = tags_match.group(1)
                tags = [t.strip().strip("'\"") for t in tag_list.split(',')]
                
                if tag in tags:
                    title = file.stem.replace("灵感-", "")
                    date_match = re.search(r'date:\s*(.+)', frontmatter_text)
                    date_str = date_match.group(1).strip() if date_match else ""
                    
                    notes.append({
                        "title": title,
                        "date": date_str,
                        "tags": tags,
                        "filename": file.name
                    })
            except Exception:
                continue
        
        notes.sort(key=lambda n: n["date"], reverse=True)
        return notes
    
    def reset_all(self):
        """重置状态并清理素材文件"""
        today = datetime.now().strftime("%Y-%m-%d")
        self.state = {
            "total_star": 0.0,
            "today_count": 0,
            "last_capture_date": "",
            "streak_days": 0,
            "active_days": 0,
            "total_notes": 0,
            "penalty_active": False,
            "penalty_days": 0,
            "medals": [],
            "monthly_medals": 0,
            "gray_medal": False,
            "last_weekly_review": "",
            "last_monthly_report": "",
            "weekly_review_done": False,
            "monthly_report_done": False,
            "completed_reports": 0,
            "exchange_history": [],
            "exchange_path": "",
            "fund_pool": 0.0,
            "fund_first_opened_at": None,
            "available_star": 0.0,
            "consumption_loss_this_month": 0.0,
            "path_streak_weeks": 0,
            "last_path_choice": "",
            "published_count": 0,
            "total_output_star": 0,
            "abilities": {
                "link_power": 0.0
            },
            "link_power_rewards_earned": [],
            "cross_domain_notes_count": 0,
            "tag_graph": {
                "nodes": {},
                "edges": {}
            },
            "current_season": {
                "id": 1,
                "name": "开拓者",
                "start_date": today,
                "end_date": "",
                "theme_tags": [],
                "star_earned_this_season": 0,
                "cross_domain_notes_this_season": 0,
                "active_days_this_season": 0
            },
            "season_history": []
        }
        self._save_state()
        
        for pattern in ["周回顾素材-*.md", "月度战报素材-*.md"]:
            for f in self.inbox_folder.glob(pattern):
                f.unlink()
        
        return {"success": True, "message": "状态已重置，素材文件已清理"}
    
    def get_current_season(self):
        """获取当前赛季信息"""
        self._load_state()
        return self.state["current_season"]
    
    def check_season_end(self):
        """检查赛季是否结束，并在结束时自动开启新赛季"""
        self._load_state()
        
        current_season = self.state["current_season"]
        if not current_season["start_date"]:
            return None
        
        season_length = self.config["seasons"].get("default_length_days", 90)
        start_date = datetime.strptime(current_season["start_date"], "%Y-%m-%d")
        end_date = start_date + timedelta(days=season_length)
        today = datetime.now().date()
        
        if today >= end_date.date():
            return self.start_new_season()
        
        return None
    
    def start_new_season(self):
        """开启新赛季"""
        self._load_state()
        
        # 赛季软重置：保留 50% 星点
        soft_reset_ratio = self.config.get("season_soft_reset_ratio", 0.5)
        carry_over = self.state["total_star"] * soft_reset_ratio
        self.state["total_star"] = carry_over
        self.state["available_star"] = carry_over
        self.state["fund_pool"] = 0.0
        self.state["fund_first_opened_at"] = None
        
        # 重置连接力赛季状态
        self.state["abilities"]["link_power"] = 0.0
        self.state["link_power_rewards_earned"] = []
        
        current_season = self.state["current_season"].copy()
        current_season["end_date"] = datetime.now().strftime("%Y-%m-%d")
        
        # 生成赛季结算报告（含"致未来自己"）
        season_report = self._generate_season_report(current_season)
        current_season["report"] = season_report
        
        self.state["season_history"].append(current_season)
        
        # 清除历史赛季中的敏感数据预测（用于对比）
        if "predictions" in current_season:
            del current_season["predictions"]
        
        themes = self.config["seasons"].get("themes", [])
        current_index = next((i for i, t in enumerate(themes) if t["id"] == current_season.get("theme_id", "pioneer")), 0)
        next_index = (current_index + 1) % len(themes)
        next_theme = themes[next_index]
        
        # 生成对下一赛季的预测
        future_predictions = self._generate_future_predictions()
        
        new_season = {
            "id": self.state["current_season"]["id"] + 1,
            "name": next_theme["name"],
            "theme_id": next_theme["id"],
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "end_date": "",
            "theme_tags": [],
            "star_earned_this_season": 0,
            "cross_domain_notes_this_season": 0,
            "active_days_this_season": 0,
            "predictions": future_predictions
        }
        
        self.state["current_season"] = new_season
        self._save_state()
        
        return {
            "old_season": current_season,
            "new_season": new_season,
            "season_report": season_report
        }
    
    def _generate_season_report(self, season):
        """生成赛季结算报告"""
        lines = []
        lines.append(f"# {season['name']} 赛季结算报告")
        lines.append("")
        lines.append(f"**赛季时间**：{season['start_date']} 至 {season.get('end_date', '进行中')}")
        lines.append("")
        
        # 数据总结
        lines.append("## 📊 赛季数据")
        lines.append("")
        lines.append(f"- 本赛季共获得 **{season.get('star_earned_this_season', 0)}** 星点")
        lines.append(f"- 跨界笔记 **{season.get('cross_domain_notes_this_season', 0)}** 篇")
        lines.append(f"- 活跃天数 **{season.get('active_days_this_season', 0)}** 天")
        lines.append("")
        
        # 星点里程碑
        total_star = self.state["total_star"]
        link_power = self.state["abilities"].get("link_power", 0)
        lines.append("## 📈 成长数据")
        lines.append("")
        lines.append(f"- 累计星点：**{total_star:.1f}**")
        lines.append(f"- 连接力：**{link_power:.1f}**")
        
        # 当前增益档位
        milestones = [500, 1000, 2000, 3000]
        current_tier = sum(1 for m in milestones if total_star >= m)
        tier_names = ["", "初露锋芒 🗡️", "采集效率提升", "输出保障", "兑换权益提升"]
        if current_tier > 0:
            lines.append(f"- 当前档位：**{tier_names[current_tier]}**（{milestones[current_tier-1]} 星点）")
        else:
            lines.append(f"- 距离「初露锋芒」还差 **{500 - total_star:.1f}** 星点")
        lines.append("")
        
        # 获得勋章
        medals = self.state["medals"]
        if medals:
            lines.append("## 🏅 获得勋章")
            lines.append("")
            for medal in medals:
                lines.append(f"- {medal}")
            lines.append("")
        
        # 致未来自己
        lines.append("## 💌 致未来的自己")
        lines.append("")
        lines.append(f"亲爱的 {season['name']}赛季的自己：")
        lines.append("")
        
        if season.get('active_days_this_season', 0) >= 60:
            lines.append("你保持了惊人的专注力，连续活跃超过60天。这份坚持终将开花结果。")
        elif season.get('active_days_this_season', 0) >= 30:
            lines.append("你建立了稳定的采集习惯，这是成长的基石。继续保持。")
        elif season.get('active_days_this_season', 0) >= 10:
            lines.append("你开始了这段旅程。每一个开始都值得尊敬。")
        else:
            lines.append("新的赛季，新的开始。无论过去如何，此刻都是重新出发的机会。")
        lines.append("")
        
        # 预测对比（如果有上一赛季的预测）
        if "predictions" in season:
            lines.append("## 🔮 预测对比")
            lines.append("")
            preds = season["predictions"]
            lines.append(f"- 当时预测赛季星点：{preds.get('predicted_star', 'N/A')}")
            lines.append(f"- 实际获得：{season.get('star_earned_this_season', 0)}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_future_predictions(self):
        """生成对未来赛季的预测"""
        # 基于当前状态预测下一赛季
        projection = self.calculate_long_term_projection(days=90)
        
        return {
            "predicted_star": projection["fund_projection"]["projected"] - self.state["fund_pool"],
            "predicted_notes": projection["notes_projection"]["projected"],
            "predicted_connections": projection["connections_projection"]["projected"],
            "generated_at": datetime.now().isoformat()
        }
    
    def get_season_history(self):
        """获取赛季历史记录"""
        self._load_state()
        return self.state["season_history"]
    
    def _update_season_stats(self, stars_earned=0, is_cross_domain=False, is_active_day=False):
        """更新赛季统计数据"""
        self._load_state()
        
        if stars_earned > 0:
            self.state["current_season"]["star_earned_this_season"] += stars_earned
        
        if is_cross_domain:
            self.state["current_season"]["cross_domain_notes_this_season"] += 1
        
        if is_active_day:
            today = self._get_today_str()
            last_active = self.state.get("_last_season_active_day", "")
            if last_active != today:
                self.state["current_season"]["active_days_this_season"] += 1
                self.state["_last_season_active_day"] = today
        
        self._save_state()
    
    def _check_season_medal(self, medal):
        """检查赛季触发类型勋章"""
        theme = medal.get("season_theme")
        if not theme:
            return False
        
        current_season = self.state["current_season"]
        return current_season.get("theme_id") == theme
    
    def reset_daily_flags(self):
        self._load_state()
        today = self._get_today_str()
        current_week = self._get_week_str()
        current_month = self._get_month_str()
        
        if self.state["last_capture_date"] != today:
            self.state["today_count"] = 0
        
        if self.state["last_weekly_review"] != current_week:
            self.state["weekly_review_done"] = False
        
        if self.state["last_monthly_report"] != current_month:
            self.state["monthly_report_done"] = False
            self.state["consumption_loss_this_month"] = 0  # 月度重置消费损失
            if not self.state["monthly_report_done"]:
                self.state["gray_medal"] = True
        
        self._save_state()