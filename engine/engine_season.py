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


class EngineSeason:

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
            "start_date": self._get_season_start_date(),
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
    

    def get_star_income_history(self):
        """获取星点获取记录"""
        self._load_state()
        return self.state.get("star_income_history", [])
    

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
    
