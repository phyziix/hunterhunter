#!/usr/bin/env python3
"""
部署验证脚本：比对 state.json 的 total_notes 与 Inbox/ 实际文件数。
灵感文件是系统最核心的数据资产，部署前后必须验证数据完整性。

用法：
    python3 verify_deployment.py [--source <数据目录路径>]

默认 source = 当前目录下的 data/inspire
"""

import argparse
import json
import sys
from pathlib import Path


def verify(source_path: Path) -> tuple[bool, int, int, list[str], list[str]]:
    """
    验证数据完整性。
    
    返回: (passed, total_notes, actual_count, state_files, inbox_files)
    """
    state_file = source_path / "_狩猎系统" / "state.json"
    inbox_dir = source_path / "Inbox"

    # 1. 读取 state.json
    if not state_file.exists():
        print(f"❌ 验证失败：state.json 不存在 ({state_file})")
        return False, 0, 0, [], []

    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ 验证失败：state.json 解析错误 ({e})")
        return False, 0, 0, [], []

    total_notes = state.get("total_notes", 0)

    # 2. 扫描 Inbox 灵感文件
    if not inbox_dir.exists():
        print(f"⚠️  Inbox 目录不存在 ({inbox_dir})，文件数计为 0")
        inbox_files = []
    else:
        inbox_files = sorted(inbox_dir.glob("灵感-*.md"))

    actual_count = len(inbox_files)
    inbox_names = [f.name for f in inbox_files]

    # 3. 比对
    passed = (total_notes == actual_count)

    if passed:
        print(f"✅ 验证通过：total_notes={total_notes}，实际文件={actual_count}")
    else:
        print(f"❌ 验证失败：total_notes={total_notes}，实际文件={actual_count}")
        diff = abs(total_notes - actual_count)
        if total_notes > actual_count:
            print(f"   缺失 {diff} 个文件（state.json 记录了 {total_notes} 条，但 Inbox 只有 {actual_count} 个 .md 文件）")
        else:
            print(f"   多余 {diff} 个文件（Inbox 有 {actual_count} 个 .md 文件，但 state.json 只记录了 {total_notes} 条）")

        print(f"\n   Inbox 实际文件列表：")
        for name in inbox_names:
            print(f"     - {name}")

    return passed, total_notes, actual_count, [], inbox_names


def main():
    parser = argparse.ArgumentParser(
        description="部署验证：比对 state.json 的笔记数与 Inbox 实际文件数"
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="数据目录路径（包含 Inbox/ 和 _狩猎系统/ 的 inspire 目录）。默认当前目录下的 data/inspire",
    )
    args = parser.parse_args()

    if args.source:
        source_path = Path(args.source).resolve()
    else:
        source_path = Path.cwd() / "data" / "inspire"

    if not source_path.exists():
        print(f"❌ 数据目录不存在：{source_path}")
        sys.exit(1)

    print(f"验证目录：{source_path}")
    passed, total_notes, actual_count, _, _ = verify(source_path)

    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
