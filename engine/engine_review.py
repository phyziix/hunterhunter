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


class EngineReview:

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

        if self.state["weekly_review_done"] and self.state["last_weekly_review"]:
            return {"error": f"本周回顾已完成（{self.state['last_weekly_review']}）"}

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
        
        self._log_star_income("周回顾", self.config["weekly_review_reward"], "完成周回顾")

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

        if self.state["monthly_report_done"] and self.state["last_monthly_report"]:
            return {"error": f"本月战报已完成（{self.state['last_monthly_report']}）"}

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
        
        self._log_star_income("月度战报", self.config["monthly_report_reward"], f"第{self.state['completed_reports']}次完成")

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
    
