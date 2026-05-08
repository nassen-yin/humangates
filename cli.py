#!/usr/bin/env python3
"""
Human Gates CLI — 管理员工具: 查看任务列表、更新状态
"""

import os
import sys
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from app.database import get_db


def list_tasks(args):
    with get_db() as db:
        if args.status:
            rows = db.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC",
                (args.status,),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?",
                (args.limit or 20,),
            ).fetchall()

    if not rows:
        print("没有任务")
        return

    print(f"{'ID':<36} {'类型':<24} {'状态':<14} {'创建时间'}")
    print("-" * 90)
    for r in rows:
        tid = r["id"][:8] + "..."
        print(f"{tid:<36} {r['type']:<24} {r['status']:<14} {r['created_at']}")


def show_task(args):
    with get_db() as db:
        row = db.execute("SELECT * FROM tasks WHERE id = ?", (args.task_id,)).fetchone()

    if not row:
        print("任务不存在")
        return

    print(f"ID:        {row['id']}")
    print(f"类型:      {row['type']}")
    print(f"状态:      {row['status']}")
    print(f"参数:      {json.dumps(json.loads(row['params']), ensure_ascii=False, indent=2)}")
    if row["result"]:
        print(f"结果:      {json.dumps(json.loads(row['result']), ensure_ascii=False, indent=2)}")
    print(f"创建时间:  {row['created_at']}")
    print(f"更新时间:  {row['updated_at']}")


def update_status(args):
    result = None
    if args.result:
        try:
            result = json.loads(args.result)
        except json.JSONDecodeError:
            print("错误: result 参数必须是有效的 JSON")
            return

    now = datetime.utcnow().isoformat()
    with get_db() as db:
        row = db.execute("SELECT * FROM tasks WHERE id = ?", (args.task_id,)).fetchone()
        if not row:
            print("任务不存在")
            return

        result_json = json.dumps(result, ensure_ascii=False) if result else None
        db.execute(
            "UPDATE tasks SET status = ?, result = ?, updated_at = ? WHERE id = ?",
            (args.status, result_json, now, args.task_id),
        )
        db.commit()
        print(f"任务 {args.task_id[:8]}... 状态已更新为: {args.status}")


def main():
    parser = argparse.ArgumentParser(description="Human Gates CLI")
    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", help="列出任务")
    p_list.add_argument("--status", help="按状态过滤 (pending/in_progress/completed/failed)")
    p_list.add_argument("--limit", type=int, help="限制数量")

    p_show = sub.add_parser("show", help="查看单个任务")
    p_show.add_argument("task_id", help="任务 ID")

    p_update = sub.add_parser("update", help="更新任务状态")
    p_update.add_argument("task_id", help="任务 ID")
    p_update.add_argument("status", help="新状态")
    p_update.add_argument("--result", help="结果 JSON")

    args = parser.parse_args()
    if args.command == "list":
        list_tasks(args)
    elif args.command == "show":
        show_task(args)
    elif args.command == "update":
        update_status(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
