import json
import os
import re
import yaml
import math
import random
import hashlib
import shutil
import time
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock


class EngineCore:

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
                "base_rate": 1.0,
                "base_bonus": 0.5,
                "lock_days": 30,
                "min_withdraw": 500
            },
            "fund_base_rate": 1.0,
            "fund_base_bonus": 0.5,
            
            # 连续选择奖惩（增量值，与基础汇率加减）
            "path_bonuses": {
                "fund": [
                    {"weeks": 2, "rate": 0.05},
                    {"weeks": 4, "rate": 0.10},
                    {"weeks": 8, "rate": 0.15}
                ],
                "coupon": [
                    {"weeks": 2, "rate": -0.05},
                    {"weeks": 4, "rate": -0.10},
                    {"weeks": 8, "rate": -0.15}
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
            "version": "0.24",  # v0.24 新增：版本号字段，用于数据迁移
            
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
            "coupon_pool": 0.0,  # 消费券兑换累计星点
            "last_exchange_date": None,  # 上次兑换日期，用于动态锁定
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
            # 标签索引：tag -> list of file_path，用于快速查询标签对应的笔记
            "tag_index": {},
            
            # 赛季系统
            "current_season": {
                "id": 1,
                "name": "开拓者",
                "start_date": self._get_season_start_date(),
                "end_date": "",
                "theme_tags": [],
                "star_earned_this_season": 0,
                "cross_domain_notes_this_season": 0,
                "active_days_this_season": 0
            },
            "season_history": [],
            # 星点获取记录
            "star_income_history": []
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
            "cross_domain_notes_count", "tag_graph", "tag_index", "current_season", "season_history",
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
        self.state.setdefault("coupon_pool", 0.0)  # 消费券兑换累计星点
        self.state.setdefault("last_exchange_date", None)  # 上次兑换日期，用于动态锁定
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
        # 标签索引
        self.state.setdefault("tag_index", {})
        
        # 赛季系统
        self.state.setdefault("completed_reports", 0)
        today = datetime.now().strftime("%Y-%m-%d")
        self.state.setdefault("current_season", {
            "id": 1,
            "name": "开拓者",
            "start_date": self._get_season_start_date(),
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
        
        # 同时初始化 tag_index
        self._init_tag_index_from_notes()
    

    def _init_tag_index_from_notes(self):
        """从现有笔记初始化 tag_index"""
        if self.state.get("tag_index", {}) and len(self.state["tag_index"]) > 0:
            return
        
        tag_index = {}
        
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
                
                for tag in tags:
                    if tag not in tag_index:
                        tag_index[tag] = []
                    file_path_str = str(file.resolve())
                    if file_path_str not in tag_index[tag]:
                        tag_index[tag].append(file_path_str)
            
            except Exception:
                continue
        
        self.state["tag_index"] = tag_index
    

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
                self._log_star_income("连接力奖励", star_reward, f"连接力达到{threshold}")
        
        return newly_earned_rewards
    

    def _load_config(self):
        # v0.24 预留：配置合并逻辑
        # 读取用户 config.yaml
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # v0.25 将从 defaults.yaml 补全缺失配置项
        # defaults = yaml.safe_load(open(defaults_path))
        # for key, value in defaults.items():
        #     config.setdefault(key, value)
        
        self.config = config
        
        # 确保 fund_base_rate 字段存在（兼容配置结构）
        if 'fund' in self.config and 'base_rate' in self.config['fund']:
            self.config['fund_base_rate'] = self.config['fund']['base_rate']
    

    def _get_data_path(self, relative_path=""):
        """v0.24 预留：数据路径解析函数"""
        # 读取配置中的数据根路径，默认为 "./data/inspire"
        data_root = self.config.get('data_root', "./data/inspire")
        if relative_path:
            return os.path.join(data_root, relative_path)
        return data_root
    

    def _load_state(self):
        with open(self.state_file, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        
        # v0.24 预留：迁移链骨架
        version = raw.get("version", "0.1")
        
        # v0.25 在此处插入迁移链
        # if version == "0.1": self._migrate_v01_to_v02(raw); version = "0.2"
        # if version == "0.2": self._migrate_v02_to_v024(raw); version = "0.24"
        # if version == "0.24": self._migrate_v024_to_v025(raw); version = "0.25"
        
        raw["version"] = version
        self.state = raw
    

    def _save_state(self):
        with self.lock:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
    

    def _save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
    

    def _get_today_str(self):
        return datetime.now().strftime("%Y-%m-%d")
    

    def _get_season_start_date(self):
        """计算赛季起始日期：每月1日、15日、16日至本月最后一日"""
        today = datetime.now()
        day = today.day
        
        if day <= 14:
            # 1-14日，赛季从本月1日开始
            return today.replace(day=1).strftime("%Y-%m-%d")
        elif day == 15:
            # 15日，赛季从15日开始
            return today.strftime("%Y-%m-%d")
        else:
            # 16日至月底，赛季从16日开始
            return today.replace(day=16).strftime("%Y-%m-%d")
    

    def _get_week_str(self):
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        return start_of_week.strftime("%Y-%W")
    

    def _get_month_str(self):
        return datetime.now().strftime("%Y-%m")
    

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
        theme = medal.get("season_theme")
        if not theme:
            return False
        
        current_season = self.state["current_season"]
        return current_season.get("theme_id") == theme
    

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
    

    def _log_star_income(self, source, amount, details=""):
        """记录星点获取"""
        self.state.setdefault("star_income_history", [])
        self.state["star_income_history"].append({
            "source": source,
            "amount": amount,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        # 只保留最近100条记录
        if len(self.state["star_income_history"]) > 100:
            self.state["star_income_history"] = self.state["star_income_history"][-100:]
    

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
            "coupon_pool": round(self.state.get("coupon_pool", 0), 2),
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
        
        self._log_star_income("内容发布", reward, f"第{self.state['published_count']}次发布")
        
        self._calculate_link_power()
        self._save_state()
        
        return {
            "reward": reward,
            "total_star": round(self.state["total_star"], 2),
            "available_star": round(self.state["available_star"], 2),
            "published_count": self.state["published_count"],
            "message": "发布成功！"
        }
    

    def get_config(self):
        # v0.2.5: 兑换模块已下线，通过配置暴露开关供前端判断
        # v0.2.5: 赛季模块已下线，通过配置暴露开关供前端判断
        config = self.config.copy()
        config["exchange_enabled"] = False  # 始终为 false，v0.4 重构后由环境变量控制
        config["season_enabled"] = False    # 始终为 false，v0.4 重构后由环境变量控制
        return config
    

    def update_config(self, updates):
        self.config.update(updates)
        self._save_config()
        return self.config
    

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
    
    # ========== 备份与 iCloud 同步 ==========
    
