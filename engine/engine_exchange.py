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


class EngineExchange:

    def _log_exchange(self, type_, amount, real_value):
        with open(self.exchange_log_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"- {timestamp} | {type_} | 扣除星点: {amount} | 实际价值: {real_value}\n")
    

    def _calculate_exchange_rate(self, path):
        """计算当前汇率（含连续选择奖惩，所有增益减益都是加减关系）"""
        path_bonuses = self.config.get("path_bonuses", {}).get(path, [])
        streak_weeks = self.state["path_streak_weeks"]
        
        if path == "fund":
            base_rate = self.config["fund"]["base_rate"]
            # 基金基础奖励（常设，任何情况下都有）
            base_bonus = self.config["fund"].get("base_bonus", 0.5)
            rate = base_rate + base_bonus
        else:
            base_rate = self.config["coupon_rate"]
            rate = base_rate
        
        # 连续选择奖惩（加减关系，path_bonuses 中存储的是增量值）
        for bonus in path_bonuses:
            if streak_weeks >= bonus["weeks"]:
                rate += bonus["rate"]
        
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
        
        # 检查动态锁定：今日是否已兑换
        today = self._get_today_str()
        last_exchange = self.state.get("last_exchange_date")
        if last_exchange == today:
            return {"error": "今日已兑换，请明天再来"}
        
        if self.state["available_star"] < amount:
            return {"error": "可用星点不足"}
        
        # 更新星点
        self.state["available_star"] -= amount
        self.state["coupon_pool"] += amount  # 记录消费兑换累计
        self.state["total_star"] = self.state["available_star"] + self.state["fund_pool"]
        self.state["last_exchange_date"] = today  # 更新最后兑换日期
        
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
        
        # 检查动态锁定：今日是否已兑换
        today = self._get_today_str()
        last_exchange = self.state.get("last_exchange_date")
        if last_exchange == today:
            return {"error": "今日已兑换，请明天再来"}
        
        if self.state["available_star"] < amount:
            return {"error": "可用星点不足"}
        
        # 检查基金门槛：最低额度
        min_withdraw = self.config["fund"].get("min_withdraw", 500)
        if amount < min_withdraw:
            return {"error": f"基金兑换最低额度为 {min_withdraw} 星点"}
        
        # 更新星点
        self.state["available_star"] -= amount
        self.state["fund_pool"] += amount
        self.state["total_star"] = self.state["available_star"] + self.state["fund_pool"]
        self.state["last_exchange_date"] = today  # 更新最后兑换日期
        
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

