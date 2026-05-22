# 状态迁移脚本

> 用于将 v0.1 版本的 state.json 迁移到 v0.22 版本的新结构。
> 运行方式：python3 migrate_state.py

import json
import os
from datetime import datetime

def get_current_date_str():
    """获取当前日期字符串 YYYY-MM-DD"""
    return datetime.now().strftime("%Y-%m-%d")

def migrate_state(old_state):
    """
    将旧状态迁移到新结构
    
    参数:
        old_state: 旧版本 state.json 的内容（dict）
    
    返回:
        新版本 state.json 的内容（dict）
    """
    new_state = {}
    
    # ========== 保留原有字段 ==========
    new_state["total_star"] = old_state.get("total_star", 0.0)
    new_state["today_count"] = old_state.get("today_count", 0)
    new_state["last_capture_date"] = old_state.get("last_capture_date", "")
    new_state["streak_days"] = old_state.get("streak_days", 0)
    new_state["penalty_active"] = old_state.get("penalty_active", False)
    new_state["penalty_days"] = old_state.get("penalty_days", 0)
    new_state["medals"] = old_state.get("medals", [])
    new_state["monthly_medals"] = old_state.get("monthly_medals", 0)
    new_state["gray_medal"] = old_state.get("gray_medal", False)
    new_state["last_weekly_review"] = old_state.get("last_weekly_review", "")
    new_state["last_monthly_report"] = old_state.get("last_monthly_report", "")
    new_state["weekly_review_done"] = old_state.get("weekly_review_done", False)
    new_state["monthly_report_done"] = old_state.get("monthly_report_done", False)
    new_state["exchange_history"] = old_state.get("exchange_history", [])
    new_state["published_count"] = old_state.get("published_count", 0)
    
    # ========== 新增字段（设置默认值） ==========
    
    # 基础状态扩展
    new_state["active_days"] = old_state.get("active_days", 0)
    new_state["total_notes"] = old_state.get("total_notes", 0)
    
    # 兑换系统
    new_state["exchange_path"] = old_state.get("exchange_path", "")
    new_state["fund_pool"] = old_state.get("fund_pool", 0.0)
    new_state["available_star"] = old_state.get("available_star", new_state["total_star"])  # 初始时可用星点 = 总星点
    new_state["consumption_loss_this_month"] = old_state.get("consumption_loss_this_month", 0.0)
    new_state["path_streak_weeks"] = old_state.get("path_streak_weeks", 0)
    new_state["last_path_choice"] = old_state.get("last_path_choice", "")
    
    # 内容输出
    new_state["total_output_star"] = old_state.get("total_output_star", 0)
    
    # 能力值系统（v0.23：仅保留连接力）
    new_state["abilities"] = old_state.get("abilities", {
        "link_power": 0.0
    })
    new_state["ability_changes"] = old_state.get("ability_changes", [])
    
    # 标签共现图
    new_state["cross_domain_notes_count"] = old_state.get("cross_domain_notes_count", 0)
    new_state["tag_graph"] = old_state.get("tag_graph", {
        "nodes": {},
        "edges": {}
    })
    
    # 赛季系统
    new_state["completed_reports"] = old_state.get("completed_reports", 0)
    new_state["current_season"] = old_state.get("current_season", {
        "id": 1,
        "name": "开拓者",
        "start_date": get_current_date_str(),
        "end_date": "",  # 后续由系统计算
        "theme_tags": [],
        "star_earned_this_season": 0,
        "cross_domain_notes_this_season": 0,
        "active_days_this_season": 0
    })
    new_state["season_history"] = old_state.get("season_history", [])
    
    return new_state

def main():
    # 定义路径
    old_state_path = "data/inspire/_狩猎系统/state.json"
    backup_path = "data/inspire/_狩猎系统/state.json.backup.v01"
    new_state_path = "data/inspire/_狩猎系统/state.json"
    
    # 检查文件是否存在
    if not os.path.exists(old_state_path):
        print(f"错误：未找到旧状态文件 {old_state_path}")
        return
    
    # 读取旧状态
    print("正在读取旧状态文件...")
    with open(old_state_path, 'r', encoding='utf-8') as f:
        old_state = json.load(f)
    
    # 备份旧状态
    print("正在备份旧状态文件...")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(old_state, f, ensure_ascii=False, indent=2)
    
    # 迁移状态
    print("正在迁移状态...")
    new_state = migrate_state(old_state)
    
    # 写入新状态
    print("正在写入新状态文件...")
    with open(new_state_path, 'w', encoding='utf-8') as f:
        json.dump(new_state, f, ensure_ascii=False, indent=2)
    
    # 统计信息
    old_keys = set(old_state.keys())
    new_keys = set(new_state.keys())
    added_keys = new_keys - old_keys
    removed_keys = old_keys - new_keys
    
    print("\n迁移完成！")
    print(f"  - 新增字段：{len(added_keys)} 个")
    print(f"    {', '.join(sorted(added_keys))}")
    print(f"  - 删除字段：{len(removed_keys)} 个（无）")
    print(f"  - 备份文件：{backup_path}")

if __name__ == "__main__":
    main()
