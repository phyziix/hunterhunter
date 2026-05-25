#!/usr/bin/env python3
"""
单向同步：本地 data/inspire/ → iCloud Obsidian Vault
规则：只写不删、不读内容、仅覆盖变更文件
"""

import shutil
from datetime import datetime
from pathlib import Path

LOCAL = Path(__file__).parent / "data" / "inspire"
ICLOUD = Path.home() / "Library" / "Mobile Documents" / "iCloud~md~obsidian" / "Documents" / "inspire"
LOG_FILE = Path(__file__).parent / "logs" / "sync.log"

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def main():
    if not LOCAL.exists():
        log(f"本地路径不存在: {LOCAL}，跳过同步")
        return

    ICLOUD.mkdir(parents=True, exist_ok=True)

    copied_count = 0
    skipped_count = 0
    copied_files = []
    skipped_files = []

    for src in sorted(LOCAL.rglob("*")):
        if src.is_dir():
            continue
        rel = src.relative_to(LOCAL)
        dst = ICLOUD / rel

        # 确保目标目录存在
        dst.parent.mkdir(parents=True, exist_ok=True)

        # 仅用元数据判断（不读文件内容）
        if dst.exists() and src.stat().st_mtime <= dst.stat().st_mtime:
            skipped_count += 1
            skipped_files.append(str(rel))
            continue

        # 只写：复制文件到 iCloud，不删除任何已有文件
        shutil.copy2(src, dst)
        copied_count += 1
        copied_files.append(str(rel))

    # 逐文件记录：写入列表
    if copied_files:
        log(f"写入 {copied_count} 个文件：")
        for f in copied_files:
            log(f"  + {f}")
    
    # 逐文件记录：跳过列表
    if skipped_files:
        log(f"跳过 {skipped_count} 个文件（目标已有且更新）：")
        for f in skipped_files:
            log(f"  = {f}")
    
    if not copied_files and not skipped_files:
        log("同步完成: 无文件变更")

if __name__ == "__main__":
    main()
