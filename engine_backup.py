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


class EngineBackup:

    def backup(self, backup_dir=None):
        """备份整个 inspire 数据目录，默认到 ~/Documents/hunterhunter_backups/，自动保留最近 10 个"""
        backup_root = Path(backup_dir) if backup_dir else Path.home() / "Documents" / "hunterhunter_backups"
        backup_root.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"inspire_backup_{timestamp}"
        backup_path = backup_root / backup_name
        
        shutil.copytree(self.base_path, backup_path)
        
        # 只保留最近 10 个备份
        existing_backups = sorted(backup_root.glob("inspire_backup_*"))
        if len(existing_backups) > 10:
            for old in existing_backups[:-10]:
                shutil.rmtree(old)
        
        file_count = sum(1 for _ in backup_path.rglob("*") if _.is_file())
        
        return {
            "success": True,
            "backup_path": str(backup_path),
            "backup_name": backup_name,
            "file_count": file_count,
            "total_backups": len(existing_backups)
        }
    

    def sync_to_icloud(self):
        """单向同步：本地 data/inspire/ → iCloud Obsidian Vault（只写不删不读内容）"""
        icloud_path = Path.home() / "Library" / "Mobile Documents" / "iCloud~md~obsidian" / "Documents" / "inspire"
        
        try:
            icloud_path.mkdir(parents=True, exist_ok=True)
        except Exception:
            return {"success": False, "error": "无法访问 iCloud 目录"}
        
        copied, skipped, errors = 0, 0, 0
        for src in sorted(self.base_path.rglob("*")):
            if src.is_dir():
                continue
            try:
                rel = src.relative_to(self.base_path)
                dst = icloud_path / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                
                # 仅比较 mtime，不读文件内容
                if dst.exists() and src.stat().st_mtime <= dst.stat().st_mtime:
                    skipped += 1
                    continue
                
                shutil.copy2(src, dst)
                copied += 1
            except Exception:
                errors += 1
        
        return {"success": True, "copied": copied, "skipped": skipped, "errors": errors}
    

    def start_icloud_sync(self, interval=300):
        """后台定时同步到 iCloud，默认每 5 分钟一次"""
        def _sync_loop():
            while True:
                time.sleep(interval)
                try:
                    self.sync_to_icloud()
                except Exception:
                    pass
        
        t = threading.Thread(target=_sync_loop, daemon=True)
        t.start()
