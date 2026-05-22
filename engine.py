import json
import os
import re
import yaml
import math
import random
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
        
        self.lock = Lock()
        
        self._init_system()
        self._load_config()
        self._load_state()
        self._migrate_state_v022()
    
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
            
            # 能力值解锁阈值
            "ability_thresholds": {
                "hunt_power": [
                    {"threshold": 30, "title": "采集达人"},
                    {"threshold": 100, "effect": "daily_multiplier_4th_upgrade"}
                ],
                "link_power": [
                    {"threshold": 5, "title": "连线新手"},
                    {"threshold": 20, "effect": "fund_bonus_extra_5"}
                ],
                "output_power": [
                    {"threshold": 10, "effect": "unlock_investment_coupon"},
                    {"threshold": 50, "effect": "output_reward_floor_850"}
                ]
            },
            
            # 赛季配置
            "seasons": {
                "default_length_days": 90,
                "auto_start": True,
                "themes": [
                    {"name": "开拓者", "id": "pioneer", "bonus": {}},
                    {"name": "连线大师", "id": "connector", "bonus": {"cross_domain_bonus": 5}},
                    {"name": "深度矿工", "id": "miner", "bonus": {"depth_bonus": 10}},
                    {"name": "分享者", "id": "sharer", "bonus": {"publish_bonus": 100}}
                ]
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
            "available_star": 0.0,
            "consumption_loss_this_month": 0.0,
            "path_streak_weeks": 0,
            "last_path_choice": "",
            
            # 内容输出
            "published_count": 0,
            "total_output_star": 0,
            
            # 能力值系统
            "abilities": {
                "hunt_power": 0.0,
                "link_power": 0.0,
                "output_power": 0.0
            },
            "ability_changes": [],
            
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
        self.state.setdefault("available_star", old_total_star)  # 初始时可用星点 = 总星点
        self.state.setdefault("consumption_loss_this_month", 0.0)
        self.state.setdefault("path_streak_weeks", 0)
        self.state.setdefault("last_path_choice", "")
        
        # 内容输出
        self.state.setdefault("total_output_star", 0)
        
        # 能力值系统
        self.state.setdefault("abilities", {
            "hunt_power": 0.0,
            "link_power": 0.0,
            "output_power": 0.0
        })
        self.state.setdefault("ability_changes", [])
        
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
        self._calculate_all_abilities()
        
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
    
    def _calculate_all_abilities(self):
        """计算所有能力值"""
        self._calculate_hunt_power()
        self._calculate_link_power()
        self._calculate_output_power()
    
    def _calculate_hunt_power(self):
        """计算采集力"""
        total_notes = self.state["total_notes"]
        active_days = self.state["active_days"]
        streak_days = self.state["streak_days"]
        
        if total_notes == 0:
            hunt_power = 5.0
        else:
            hunt_power = (total_notes ** 0.7) * math.log(active_days + 1) * (1 + streak_days / 100)
        
        # 限制范围 5~200
        hunt_power = max(5.0, min(200.0, hunt_power))
        
        old_value = self.state["abilities"]["hunt_power"]
        change = hunt_power - old_value
        self.state["abilities"]["hunt_power"] = hunt_power
        
        if abs(change) > 0.01:
            self._update_ability_changes("hunt_power", change, "采集力计算更新")
    
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
        
        old_value = self.state["abilities"]["link_power"]
        change = link_power - old_value
        self.state["abilities"]["link_power"] = link_power
        
        if abs(change) > 0.01:
            self._update_ability_changes("link_power", change, "连接力计算更新")
    
    def _calculate_output_power(self):
        """计算输出力"""
        published_count = self.state.get("published_count", 0)
        completed_reports = self.state.get("completed_reports", 0)
        total_output_star = self.state.get("total_output_star", 0)
        
        if published_count == 0:
            output_power = 0.0
        else:
            output_power = (published_count ** 0.6) * (1 + completed_reports / 10) * math.log(total_output_star + 1)
        
        # 限制范围 0~100
        output_power = max(0.0, min(100.0, output_power))
        
        old_value = self.state["abilities"]["output_power"]
        change = output_power - old_value
        self.state["abilities"]["output_power"] = output_power
        
        if abs(change) > 0.01:
            self._update_ability_changes("output_power", change, "输出力计算更新")
    
    def _update_ability_changes(self, ability, change, reason):
        """维护能力值变更日志"""
        change_entry = {
            "date": datetime.now().isoformat(),
            "ability": ability,
            "change": round(change, 2),
            "reason": reason
        }
        
        self.state["ability_changes"].append(change_entry)
        
        # 只保留最近7天的记录
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        self.state["ability_changes"] = [
            entry for entry in self.state["ability_changes"]
            if entry["date"] >= seven_days_ago
        ]
    
    def _load_config(self):
        with open(self.config_file, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
    
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
    
    def _check_medals(self):
        medals = set(self.state["medals"])
        
        if self.state["today_count"] >= 3 and "灵光乍现" not in medals:
            self.state["medals"].append("灵光乍现")
        
        streak = self.state["streak_days"]
        if streak >= 7 and "周常猎人" not in medals:
            self.state["medals"].append("周常猎人")
        
        # 能力值相关勋章
        hunt_power = self.state["abilities"]["hunt_power"]
        link_power = self.state["abilities"]["link_power"]
        
        if hunt_power >= 30 and "采集达人" not in medals:
            self.state["medals"].append("采集达人")
        
        if link_power >= 5 and "连线新手" not in medals:
            self.state["medals"].append("连线新手")
        
        self.state["medals"] = list(set(self.state["medals"]))
    
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
        today = self._get_today_str()
        
        self._load_state()
        
        if self.state["last_capture_date"] != today:
            self.state["today_count"] = 0
            self._check_streak()
        
        self.state["today_count"] += 1
        
        stars = self._calculate_stars()
        self.state["available_star"] += stars
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
        
        self._update_tag_graph(tags)
        self.state["total_notes"] += 1
        
        self._calculate_all_abilities()
        self._check_medals()
        self._save_state()
        
        return {
            "earned": round(stars, 2),
            "total_star": round(self.state["total_star"], 2),
            "available_star": round(self.state["available_star"], 2),
            "today_count": self.state["today_count"],
            "streak_days": self.state["streak_days"],
            "abilities": {k: round(v, 2) for k, v in self.state["abilities"].items()},
            "message": "捕获成功！"
        }
    
    def get_status(self):
        self._load_state()
        return {
            "total_star": round(self.state["total_star"], 2),
            "available_star": round(self.state["available_star"], 2),
            "fund_pool": round(self.state["fund_pool"], 2),
            "today_count": self.state["today_count"],
            "streak_days": self.state["streak_days"],
            "medals": self.state["medals"],
            "monthly_medals": self.state["monthly_medals"],
            "gray_medal": self.state["gray_medal"],
            "weekly_review_done": self.state["weekly_review_done"],
            "monthly_report_done": self.state["monthly_report_done"],
            "published_count": self.state.get("published_count", 0),
            "exchange_path": self.state["exchange_path"],
            "path_streak_weeks": self.state["path_streak_weeks"],
            "consumption_loss_this_month": round(self.state["consumption_loss_this_month"], 2),
            "abilities": {k: round(v, 2) for k, v in self.state["abilities"].items()},
            "ability_changes": self.state["ability_changes"],
            "current_season": self.state["current_season"],
            "total_notes": self.state["total_notes"],
            "active_days": self.state["active_days"]
        }
    
    def process_publish(self, url):
        self._load_state()
        self._load_config()
        
        max_times = self.config.get("content_output_max_times", 5)
        if self.state.get("published_count", 0) >= max_times:
            return {"error": f"已达到最大发布次数（{max_times}次）"}
        
        min_reward = self.config.get("content_output_reward_min", 750)
        max_reward = self.config.get("content_output_reward_max", 1000)
        
        # 检查输出力阈值加成
        output_power = self.state["abilities"]["output_power"]
        if output_power >= 50:
            min_reward = 850
        
        reward = int(min_reward + (max_reward - min_reward) * random.random())
        
        if "published_count" not in self.state:
            self.state["published_count"] = 0
        self.state["published_count"] += 1
        self.state["total_output_star"] += reward
        self.state["available_star"] += reward
        self.state["total_star"] = self.state["available_star"] + self.state["fund_pool"]
        
        self._calculate_all_abilities()
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
        
        # 检查基金门槛
        min_withdraw = self.config["fund"].get("min_withdraw", 500)
        if amount < min_withdraw:
            return {"error": f"基金兑换最低额度为 {min_withdraw} 星点"}
        
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
        lines = [
            f"# {title}",
            "",
            f"> 时间范围：{date_range_label}",
            f"> 共 {len(notes)} 条灵感碎片",
            "",
            "## 本周灵感碎片" if "周" in title else "## 本月灵感碎片",
            ""
        ]

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

        self._calculate_all_abilities()
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

        tag_count = len(tags)
        if tag_count >= 3 and "连线大师" not in self.state["medals"]:
            self.state["medals"].append("连线大师")

        self.state["last_monthly_report"] = current_month
        self.state["monthly_report_done"] = True
        self.state["completed_reports"] += 1
        self.state["available_star"] += self.config["monthly_report_reward"]
        self.state["total_star"] = self.state["available_star"] + self.state["fund_pool"]

        self._calculate_all_abilities()
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
            "available_star": 0.0,
            "consumption_loss_this_month": 0.0,
            "path_streak_weeks": 0,
            "last_path_choice": "",
            "published_count": 0,
            "total_output_star": 0,
            "abilities": {
                "hunt_power": 0.0,
                "link_power": 0.0,
                "output_power": 0.0
            },
            "ability_changes": [],
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