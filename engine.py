import json
import os
import yaml
import time
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
            "fund_base_rate": 1.5,
            "custom_fund_name": "我的投资账户"
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
    
    def _write_default_state(self):
        default_state = {
            "total_star": 0.0,
            "today_count": 0,
            "last_capture_date": "",
            "streak_days": 0,
            "penalty_active": False,
            "penalty_days": 0,
            "medals": [],
            "monthly_medals": 0,
            "gray_medal": False,
            "last_weekly_review": "",
            "last_monthly_report": "",
            "weekly_review_done": False,
            "monthly_report_done": False,
            "exchange_history": [],
            "published_count": 0
        }
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(default_state, f, ensure_ascii=False, indent=2)
    
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
            return
        
        last_dt = datetime.strptime(last_date, "%Y-%m-%d")
        today_dt = datetime.strptime(today, "%Y-%m-%d")
        diff_days = (today_dt - last_dt).days
        
        if diff_days == 1:
            self.state["streak_days"] += 1
        elif diff_days > 1:
            self.state["streak_days"] = 1
        
        self.state["last_capture_date"] = today
    
    def _check_penalty(self):
        today = datetime.now()
        last_date = self.state["last_capture_date"]
        
        if not last_date:
            return
        
        last_dt = datetime.strptime(last_date, "%Y-%m-%d")
        diff_days = (today - last_dt).days
        
        if diff_days >= 3 and not self.state["penalty_active"]:
            self.state["penalty_active"] = True
            self.state["penalty_days"] = 0
        elif self.state["penalty_active"]:
            self.state["penalty_days"] += 1
            if self.state["penalty_days"] >= 3:
                self.state["penalty_active"] = False
                self.state["penalty_days"] = 0
    
    def _calculate_stars(self):
        count = self.state["today_count"]
        multipliers = self.config["daily_multipliers"]
        
        if count <= len(multipliers):
            multiplier = multipliers[count - 1]
        else:
            multiplier = multipliers[-1]
        
        base = self.config["base_star"]
        stars = base * multiplier
        
        if self.state["penalty_active"]:
            stars *= 0.5
        
        return stars
    
    def _check_medals(self):
        medals = set(self.state["medals"])
        
        if self.state["today_count"] >= 3 and "灵光乍现" not in medals:
            self.state["medals"].append("灵光乍现")
        
        streak = self.state["streak_days"]
        if streak >= 7 and "周常猎人" not in medals:
            self.state["medals"].append("周常猎人")
        
        self.state["medals"] = list(set(self.state["medals"]))
    
    def _log_exchange(self, type_, amount, real_value):
        with open(self.exchange_log_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"- {timestamp} | {type_} | 扣除星点: {amount} | 实际价值: {real_value}\n")
    
    def process_daily_capture(self, content, tags=None, folder="Inbox"):
        tags = tags or []
        today = self._get_today_str()
        
        self._load_state()
        
        if self.state["last_capture_date"] != today:
            self.state["today_count"] = 0
            self._check_streak()
            self._check_penalty()
        
        self.state["today_count"] += 1
        
        stars = self._calculate_stars()
        self.state["total_star"] += stars
        
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
        
        self._check_medals()
        self._save_state()
        
        return {
            "earned": stars,
            "total_star": self.state["total_star"],
            "today_count": self.state["today_count"],
            "message": "捕获成功！"
        }
    
    def get_status(self):
        self._load_state()
        return {
            "total_star": self.state["total_star"],
            "today_count": self.state["today_count"],
            "streak_days": self.state["streak_days"],
            "penalty_active": self.state["penalty_active"],
            "medals": self.state["medals"],
            "monthly_medals": self.state["monthly_medals"],
            "gray_medal": self.state["gray_medal"],
            "fund_bonus": min(self.state["monthly_medals"] * 5, 25),
            "weekly_review_done": self.state["weekly_review_done"],
            "monthly_report_done": self.state["monthly_report_done"],
            "published_count": self.state.get("published_count", 0)
        }
    
    def process_publish(self, url):
        self._load_state()
        self._load_config()
        
        max_times = self.config.get("content_output_max_times", 5)
        if self.state.get("published_count", 0) >= max_times:
            return {"error": f"已达到最大发布次数（{max_times}次）"}
        
        min_reward = self.config.get("content_output_reward_min", 750)
        max_reward = self.config.get("content_output_reward_max", 1000)
        reward = int(min_reward + (max_reward - min_reward) * random.random())
        
        if "published_count" not in self.state:
            self.state["published_count"] = 0
        self.state["published_count"] += 1
        self.state["total_star"] += reward
        
        self._save_state()
        
        return {
            "reward": reward,
            "total_star": self.state["total_star"],
            "published_count": self.state["published_count"],
            "message": "发布成功！"
        }
    
    def exchange(self, type_, amount):
        self._load_state()
        
        if self.state["total_star"] < amount:
            return {"error": "星点不足"}
        
        self.state["total_star"] -= amount
        
        if type_ == "coupon":
            real_value = amount * self.config["coupon_rate"]
        elif type_ == "fund":
            bonus = min(self.state["monthly_medals"] * 5, 25) / 100
            real_value = amount * self.config["fund_base_rate"] * (1 + bonus)
        else:
            return {"error": "未知兑换类型"}
        
        self._log_exchange(type_, amount, real_value)
        
        self.state["exchange_history"].append({
            "type": type_,
            "amount": amount,
            "real_value": real_value,
            "timestamp": datetime.now().isoformat()
        })
        
        self._save_state()
        
        return {
            "deducted_star": amount,
            "real_value": real_value,
            "new_balance": self.state["total_star"],
            "message": "请手动转账"
        }
    
    def weekly_review(self, confirmed=True, insight=""):
        self._load_state()
        
        current_week = self._get_week_str()
        
        if self.state["last_weekly_review"] == current_week:
            return {"error": "本周已完成回顾"}
        
        self.state["last_weekly_review"] = current_week
        self.state["weekly_review_done"] = True
        self.state["total_star"] += self.config["weekly_review_reward"]
        
        self._save_state()
        
        return {
            "reward": self.config["weekly_review_reward"],
            "new_balance": self.state["total_star"],
            "message": "周回顾完成！"
        }
    
    def monthly_report(self, confirmed=True, insight=""):
        self._load_state()
        
        current_month = self._get_month_str()
        
        if self.state["last_monthly_report"] == current_month:
            return {"error": "本月已完成战报"}
        
        if self.state["gray_medal"]:
            self.state["gray_medal"] = False
        else:
            self.state["monthly_medals"] += 1
        
        self.state["last_monthly_report"] = current_month
        self.state["monthly_report_done"] = True
        self.state["total_star"] += self.config["monthly_report_reward"]
        
        tag_count = self._count_monthly_tags(current_month)
        if tag_count >= 3 and "连线大师" not in self.state["medals"]:
            self.state["medals"].append("连线大师")
        
        self._save_state()
        
        return {
            "reward": self.config["monthly_report_reward"],
            "new_balance": self.state["total_star"],
            "monthly_medals": self.state["monthly_medals"],
            "message": "月度战报完成！"
        }
    
    def _count_monthly_tags(self, month_str):
        tags = set()
        month_dt = datetime.strptime(month_str, "%Y-%m")
        
        for file in self.inbox_folder.glob("灵感-*.md"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'hunt: true' in content:
                        lines = content.split('\n')
                        in_frontmatter = False
                        for line in lines:
                            if line.startswith('---'):
                                in_frontmatter = not in_frontmatter
                            elif in_frontmatter and line.startswith('date:'):
                                date_str = line.split(':')[1].strip()
                                try:
                                    file_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                    if file_date.year == month_dt.year and file_date.month == month_dt.month:
                                        for tag_line in lines:
                                            if tag_line.startswith('tags:'):
                                                tag_content = tag_line.split(':', 1)[1].strip()
                                                if tag_content.startswith('[') and tag_content.endswith(']'):
                                                    tag_list = eval(tag_content)
                                                    tags.update(tag_list)
                                except:
                                    continue
            except:
                continue
        
        return len(tags)
    
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
            if not self.state["monthly_report_done"]:
                self.state["gray_medal"] = True
        
        self._save_state()
