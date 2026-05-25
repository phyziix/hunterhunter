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


class EngineCapture:

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
        
        # 计算星点（含倍增阶梯 + 连续加成）
        total_stars = self._calculate_stars()
        
        # 提取展示用拆分明细
        base_star = self.config.get("base_star", 10)
        multipliers = self.config.get("daily_multipliers", [1.0, 1.5, 2.0, 0.2])
        count = self.state["today_count"]
        mult = multipliers[count - 1] if count <= len(multipliers) else multipliers[-1]
        base_stars = base_star * mult
        
        streak_bonus_pct = 0
        streak_days = self.state["streak_days"]
        if count == 1:  # 连续加成只有第1条触发
            for bonus in reversed(self.config.get("streak_bonuses", [])):
                if streak_days >= bonus["days"]:
                    streak_bonus_pct = bonus["bonus_pct"]
                    break
        
        streak_bonus_amount = total_stars - base_stars if streak_bonus_pct > 0 else 0.0
        
        self.state["available_star"] += total_stars
        self.state["total_star"] = self.state["available_star"] + self.state["fund_pool"]
        
        # 记录星点获取
        details = f"基础{base_stars} + 连续奖励{streak_bonus_amount:.1f}（{streak_days}天）"
        self._log_star_income("灵感采集", total_stars, details)
        
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
        
        # 保存原始内容用于去重和相似笔记匹配
        original_content = content
        
        # 去重检测
        dup_result = self._check_duplicate(original_content, folder_path)
        if dup_result:
            return dup_result
        
        content = "\n".join(frontmatter_lines) + "\n\n" + content
        
        file_fullpath = folder_path / filename
        with open(file_fullpath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 记录灵感文件创建（仅在实际写入成功后，用于追溯验证）
        self._log_event("FILE_CREATED", "灵感文件已创建", {
            "文件名": filename,
            "路径": str(file_fullpath.resolve()),
            "文件大小": f"{len(content)} 字符",
            "标签": ", ".join(tags),
            "本次星点": total_stars,
            "今日第几条": self.state["today_count"]
        })
        
        # 记录添加标签前的边数用于检测新连接
        old_edges_count = sum(self.state["tag_graph"]["edges"].values())
        
        self._update_tag_graph(tags)
        
        # 更新 tag_index
        file_path_str = str((folder_path / filename).resolve())
        for tag in tags:
            if tag not in self.state["tag_index"]:
                self.state["tag_index"][tag] = []
            if file_path_str not in self.state["tag_index"][tag]:
                self.state["tag_index"][tag].append(file_path_str)
        
        # 检测新产生的标签连接
        new_edges_count = sum(self.state["tag_graph"]["edges"].values())
        new_connections = self._find_new_connections(tags) if (new_edges_count > old_edges_count) else []
        
        self.state["total_notes"] += 1
        
        self._calculate_link_power()
        link_power_rewards = self._check_link_power_rewards()
        self._check_medals()
        self._save_state()
        
        # 查找相似笔记
        related_notes = self._find_related_notes(tags, content=original_content, limit=3)
        
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
    

    def _find_related_notes(self, tags, content="", limit=3):
        """查找相似笔记（基于标签IDF加权Jaccard + 内容相似度）"""
        related_notes = []
        inbox_folder = self.base_path / "Inbox"
        
        if not inbox_folder.exists():
            return related_notes
        
        tag_set = set([t.strip('#').lower() for t in tags if t.strip()])
        if not tag_set:
            return related_notes
        
        # 对输入内容做简单分词（中文2字词、英文3字母词）
        input_words = set()
        if content:
            input_words = set(re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', content.lower()))
        
        # 第一遍扫描：统计所有标签出现频率（用于IDF加权）
        all_tag_counts = {}
        total_docs = 0
        note_metas = []  # 缓存解析结果避免二次IO
        
        for note_file in inbox_folder.glob("*.md"):
            total_docs += 1
            try:
                with open(note_file, 'r', encoding='utf-8') as f:
                    note_content = f.read()
                
                if note_content.startswith("---"):
                    end = note_content.find("\n---\n", 4)
                    if end != -1:
                        frontmatter = note_content[4:end]
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
                        if not note_tag_set:
                            continue
                        
                        body = note_content[end+4:].strip()
                        nl = body.find('\n')
                        body = body[nl+1:].strip() if nl != -1 else ""
                        
                        note_metas.append({
                            "file": note_file,
                            "tag_set": note_tag_set,
                            "body": body,
                        })
                        
                        for t in note_tag_set:
                            all_tag_counts[t] = all_tag_counts.get(t, 0) + 1
            except:
                continue
        
        if total_docs == 0:
            return related_notes
        
        # 计算IDF权重：log(总文档数 / 该标签出现次数)，高频标签权重低
        import math
        tag_idf = {}
        for t, count in all_tag_counts.items():
            idf = math.log((total_docs + 1) / (count + 1)) + 1  # +1避免0
            tag_idf[t] = min(idf, 5.0)  # IDF 上限截断，防止冷门标签权重爆炸
        
        # 第二遍：用IDF加权计算匹配度
        for meta in note_metas:
            note_tag_set = meta["tag_set"]
            body = meta["body"]
            note_file = meta["file"]
            
            overlap = len(tag_set & note_tag_set)
            if overlap == 0:
                continue
            
            # IDF加权Jaccard：交集权重之和 / 并集权重之和
            intersection_weight = sum(tag_idf.get(t, 1.0) for t in (tag_set & note_tag_set))
            union_weight = sum(tag_idf.get(t, 1.0) for t in (tag_set | note_tag_set))
            tag_jaccard_idf = intersection_weight / union_weight if union_weight > 0 else 0
            
            # 内容相似度
            note_words = set(re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', body[:500].lower()))
            all_words = input_words | note_words
            content_jaccard = len(input_words & note_words) / len(all_words) if all_words else 0
            
            # 综合得分：标签权重 0.7，内容权重 0.3
            score = tag_jaccard_idf * 0.7 + content_jaccard * 0.3
            
            # 阈值规则：
            # 1. 标签重叠≥2 且 综合得分≥0.2（保留原规则）
            # 2. 标签重叠=1 且 综合得分≥0.25（新增规则，支持单标签新笔记）
            if (overlap >= 2 and score >= 0.2) or (overlap == 1 and score >= 0.25):
                title = body.split('\n')[0][:40] if body else ""
                if not title:
                    title = note_file.stem.replace("灵感-", "").split("-")[-1]
                
                snippet = body[:500]
                
                related_notes.append({
                    "title": title,
                    "date": note_file.stem.split("-")[1] if "-" in note_file.stem else "",
                    "file_path": str(note_file),
                    "tag_overlap": overlap,
                    "score": round(score, 3),
                    "snippet": snippet
                })
        
        # 排序：综合得分第一，标签重叠数第二
        related_notes.sort(key=lambda x: (x["score"], x["tag_overlap"]), reverse=True)
        return related_notes[:limit]
    

    def _check_duplicate(self, content, folder_path):
        """检查是否与已有笔记重复"""
        # 标准化内容：去除空白、取前200字做指纹
        normalized = re.sub(r'\s+', '', content)[:200]
        if len(normalized) < 20:
            return None  # 太短不检查
        
        for note_file in folder_path.glob("*.md"):
            try:
                with open(note_file, 'r', encoding='utf-8') as f:
                    existing = f.read()
                
                # 提取正文（跳过 frontmatter）
                if existing.startswith("---"):
                    end = existing.find("\n---\n", 4)
                    if end != -1:
                        existing_body = existing[end+4:].strip()
                        # 跳过标题行
                        nl = existing_body.find('\n')
                        existing_body = existing_body[nl+1:].strip() if nl != -1 else existing_body
                        existing_normalized = re.sub(r'\s+', '', existing_body)[:200]
                        
                        # 完全相同
                        if normalized == existing_normalized:
                            return {
                                "error": "已存在相同内容的笔记，请勿重复提交",
                                "detail": f"与 {note_file.name} 内容一致"
                            }
                        
                        # 高相似度（>85% 逐字匹配）
                        if len(normalized) > 40 and len(existing_normalized) > 40:
                            min_len = min(len(normalized), len(existing_normalized))
                            match_chars = sum(1 for i in range(min_len) if normalized[i] == existing_normalized[i])
                            similarity = match_chars / min_len
                            if similarity > 0.85:
                                return {
                                    "error": "存在高度相似的笔记，请检查是否重复提交",
                                    "detail": f"与 {note_file.name} 相似度 {similarity:.0%}"
                                }
            except:
                continue
        return None
    

    def get_tag_cloud_data(self):
        """返回标签云数据"""
        self._load_state()
        return {
            "nodes": self.state["tag_graph"]["nodes"],
            "edges": self.state["tag_graph"]["edges"]
        }
    

    def get_notes_by_tag(self, tag):
        """按标签查询笔记（使用 tag_index 优化性能）"""
        notes = []
        self._load_state()
        
        # 如果 tag_index 为空或该标签不存在，先初始化索引
        if (not self.state.get("tag_index") or 
            len(self.state["tag_index"]) == 0 or 
            tag not in self.state["tag_index"]):
            self._init_tag_index_from_notes()
            self._save_state()
        
        # 从 tag_index 获取文件列表
        file_paths = self.state["tag_index"].get(tag, [])
        
        for file_path_str in file_paths:
            try:
                file = Path(file_path_str)
                if not file.exists():
                    continue
                
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
                
                title = file.stem.replace("灵感-", "")
                date_match = re.search(r'date:\s*(.+)', frontmatter_text)
                date_str = date_match.group(1).strip() if date_match else ""
                
                notes.append({
                    "title": title,
                    "date": date_str,
                    "tags": tags,
                    "file_path": file_path_str
                })
            except Exception:
                continue
        
        notes.sort(key=lambda n: n["date"], reverse=True)
        return notes
    

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
    
