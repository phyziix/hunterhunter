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
    

    def _calculate_path_streak_bonus(self, path):
        """计算连续选择路径的奖励加成
        
        基金用户：连续2周 +0.05、连续4周 +0.10、连续8周 +0.15
        消费用户：连续2周 -0.05、连续4周 -0.10、连续8周 -0.15
        中断（切换路径）则加成归零
        """
        streak_weeks = self.state.get("path_streak_weeks", 0)
        bonuses = self.config.get("path_bonuses", {}).get(path, [])
        
        bonus = 0
        for b in bonuses:
            if streak_weeks >= b["weeks"]:
                bonus += b["rate"]
        
        return bonus
    
    def _calculate_exchange_rate(self, path):
        """计算当前汇率（所有增益减益都是加减关系）"""
        if path == "fund":
            # 基金：固定基础倍率 1.0 + 常设基础奖励 0.5 + 连续选择加成
            rate = self.config["fund"]["base_rate"] + self.config["fund"].get("base_bonus", 0.5)
            rate += self._calculate_path_streak_bonus("fund")
        else:
            # 消费：基础倍率 + 连续选择惩罚
            rate = self.config["coupon_rate"] + self._calculate_path_streak_bonus("coupon")
        
        return rate
    
    def _update_path_streak(self, path):
        """更新路径连续选择计数"""
        last_choice = self.state.get("exchange_path", "")
        last_week = self._get_week_str()
        
        if last_choice == path:
            self.state["path_streak_weeks"] += 1
        else:
            self.state["path_streak_weeks"] = 0
        
        self.state["exchange_path"] = path
        self.state["last_path_choice"] = last_week
    
    def calculate_opportunity_cost(self, amount, from_path):
        """三层镜像对比
        
        等值对比：消费金额 vs 基金金额
        时间维度延伸：基金增值预估 / 消费品折旧
        历史累计：本月消费损失或克制收益
        """
        fund_rate = self._calculate_exchange_rate("fund")
        coupon_rate = self._calculate_exchange_rate("coupon")
        
        fund_value = amount * fund_rate
        coupon_value = amount * coupon_rate
        
        # 时间维度延伸：基金增值预估（假设持有1个月）
        monthly_fund_growth = fund_value * 0.05  # 月增长率约5%
        
        # 消费品折旧（假设1个月折旧10%）
        monthly_coupon_depreciation = coupon_value * 0.10
        
        return {
            # 第一层：等值对比
            "equivalent_comparison": {
                "coupon_value": round(coupon_value, 2),
                "fund_value": round(fund_value, 2),
                "difference": round(fund_value - coupon_value, 2)
            },
            # 第二层：时间维度延伸
            "time_dimension": {
                "fund_monthly_growth": round(monthly_fund_growth, 2),
                "coupon_monthly_depreciation": round(monthly_coupon_depreciation, 2)
            },
            # 第三层：历史累计
            "historical_accumulation": {
                "consumption_loss_this_month": round(self.state.get("consumption_loss_this_month", 0), 2),
                "fund_gain_this_month": round(self.state.get("fund_gain_this_month", 0), 2)
            }
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
        """消费兑换"""
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
        
        # 更新本月基金增益
        coupon_rate = self._calculate_exchange_rate("coupon")
        fund_gain = amount * (rate - coupon_rate)
        self.state["fund_gain_this_month"] = self.state.get("fund_gain_this_month", 0) + fund_gain
        
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
    
    # ========== 消费记录功能 ==========
    
    def record_consumption(self, content: str, amount: float):
        """记录一笔消费
        
        从已兑换消费额中扣减相应金额
        
        Args:
            content: 消费内容描述
            amount: 消费金额
            
        Returns:
            dict: 操作结果
        """
        self._load_state()
        
        # 计算已兑换消费额和已消费金额的差值（剩余可用额度）
        coupon_pool = self.state.get("coupon_pool", 0)  # 已兑换消费额
        consumed_amount = self.state.get("consumed_amount", 0)  # 已消费
        remaining = coupon_pool - consumed_amount
        
        # 校验额度
        if amount > remaining:
            return {
                "success": False,
                "error": f"额度不足，当前剩余 ¥{remaining:.2f}",
                "remaining": round(remaining, 2)
            }
        
        # 更新已消费金额
        self.state["consumed_amount"] = consumed_amount + amount
        
        # 记录消费条目
        if "consumption_records" not in self.state:
            self.state["consumption_records"] = []
        
        self.state["consumption_records"].append({
            "content": content,
            "amount": amount,
            "timestamp": datetime.now().isoformat()
        })
        
        self._save_state()
        
        new_remaining = coupon_pool - self.state["consumed_amount"]
        
        return {
            "success": True,
            "consumed_amount": round(self.state["consumed_amount"], 2),
            "remaining": round(new_remaining, 2),
            "record": {
                "content": content,
                "amount": amount,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def get_consumption_history(self):
        """获取消费记录列表
        
        Returns:
            dict: 包含消费记录和统计信息
        """
        self._load_state()
        
        consumed_amount = self.state.get("consumed_amount", 0)
        coupon_pool = self.state.get("coupon_pool", 0)
        records = self.state.get("consumption_records", [])
        
        return {
            "consumed_amount": round(consumed_amount, 2),
            "coupon_pool": round(coupon_pool, 2),
            "remaining": round(coupon_pool - consumed_amount, 2),
            "records": records
        }
    
    # ========== 回顾与战报：两步流程 ==========

