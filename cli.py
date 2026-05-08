#!/usr/bin/env python3
"""
Human Gates CLI — 管理员工具: 查看任务列表、更新状态、管理文件、查看时间线
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

    print(f"{'ID':<36} {'类型':<24} {'状态':<16} {'创建时间'}")
    print("-" * 96)
    for r in rows:
        tid = r["id"][:8] + "..."
        print(f"{tid:<36} {r['type']:<24} {r['status']:<16} {r['created_at']}")


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

        # 显示文件
        files = db.execute(
            "SELECT file_name, file_type, file_size FROM files WHERE task_id = ?",
            (args.task_id,),
        ).fetchall()
        if files:
            print(f"\n文件 ({len(files)}):")
            for f in files:
                size_kb = f["file_size"] / 1024
                print(f"  [{f['file_type']}] {f['file_name']} ({size_kb:.1f}KB)")

        # 显示时间线摘要
        logs = db.execute(
            "SELECT action, note, created_at FROM task_logs WHERE task_id = ? ORDER BY id DESC LIMIT 5",
            (args.task_id,),
        ).fetchall()
        if logs:
            print(f"\n最近操作 ({len(logs)}):")
            for log in logs:
                note = f" — {log['note'][:50]}" if log["note"] else ""
                print(f"  [{log['created_at'][:19]}] {log['action']}{note}")


def update_status(args):
    result = None
    if args.result:
        try:
            result = json.loads(args.result)
        except json.JSONDecodeError:
            print("错误: result 参数必须是有效的 JSON")
            return

    note = args.note or None
    now = datetime.utcnow().isoformat()

    with get_db() as db:
        row = db.execute("SELECT * FROM tasks WHERE id = ?", (args.task_id,)).fetchone()
        if not row:
            print("任务不存在")
            return

        old_status = row["status"]
        from app.models import get_valid_transitions
        allowed = get_valid_transitions(old_status)
        if args.status not in allowed:
            print(f"状态转换非法: {old_status} → {args.status}")
            print(f"允许: {', '.join(allowed) if allowed else '无（终态）'}")
            return

        result_json = json.dumps(result, ensure_ascii=False) if result else None
        db.execute(
            "UPDATE tasks SET status = ?, result = ?, updated_at = ? WHERE id = ?",
            (args.status, result_json, now, args.task_id),
        )
        # 写日志
        db.execute(
            "INSERT INTO task_logs (task_id, action, note, old_status, new_status) VALUES (?, 'status_change', ?, ?, ?)",
            (args.task_id, note, old_status, args.status),
        )
        db.commit()
        print(f"任务 {args.task_id[:8]}... {old_status} → {args.status}")


def list_files(args):
    with get_db() as db:
        row = db.execute("SELECT id FROM tasks WHERE id = ?", (args.task_id,)).fetchone()
        if not row:
            print("任务不存在")
            return

        files = db.execute(
            "SELECT id, file_name, file_type, file_size, uploaded_at FROM files WHERE task_id = ? ORDER BY uploaded_at",
            (args.task_id,),
        ).fetchall()

    if not files:
        print("该任务没有上传文件")
        return

    print(f"{'ID':<6} {'类型':<18} {'文件名':<30} {'大小':<10} {'上传时间'}")
    print("-" * 90)
    for f in files:
        size_str = f"{f['file_size']/1024:.1f}KB" if f['file_size'] > 1024 else f"{f['file_size']}B"
        print(f"{f['id']:<6} {f['file_type']:<18} {f['file_name']:<30} {size_str:<10} {f['uploaded_at'][:19]}")


def timeline(args):
    with get_db() as db:
        row = db.execute("SELECT id FROM tasks WHERE id = ?", (args.task_id,)).fetchone()
        if not row:
            print("任务不存在")
            return

        logs = db.execute(
            "SELECT action, note, old_status, new_status, created_at FROM task_logs WHERE task_id = ? ORDER BY id ASC",
            (args.task_id,),
        ).fetchall()

    if not logs:
        print("该任务没有操作记录")
        return

    print(f"任务时间线: {args.task_id[:16]}...")
    print("-" * 60)
    for log in logs:
        ts = log["created_at"][:19]
        action = log["action"]
        if action == "status_change":
            status_str = f"{log['old_status']} → {log['new_status']}"
            note = f" — {log['note']}" if log["note"] else ""
            print(f"  [{ts}] {status_str}{note}")
        elif action == "note":
            note = log["note"] or ""
            print(f"  [{ts}] 备注: {note}")
        else:
            note = f" — {log['note']}" if log["note"] else ""
            print(f"  [{ts}] {action}{note}")


def add_note(args):
    with get_db() as db:
        row = db.execute("SELECT id FROM tasks WHERE id = ?", (args.task_id,)).fetchone()
        if not row:
            print("任务不存在")
            return
        db.execute(
            "INSERT INTO task_logs (task_id, action, note) VALUES (?, 'note', ?)",
            (args.task_id, args.note_text),
        )
        db.commit()
    print("备注已添加")


def main():
    parser = argparse.ArgumentParser(description="Human Gates CLI")
    sub = parser.add_subparsers(dest="command")

    # list
    p_list = sub.add_parser("list", help="列出任务")
    p_list.add_argument("--status", help="按状态过滤 (pending_review/needs_info/materials_ready/in_progress/completed/failed)")
    p_list.add_argument("--limit", type=int, help="限制数量")

    # show
    p_show = sub.add_parser("show", help="查看单个任务（含文件和时间线摘要）")
    p_show.add_argument("task_id", help="任务 ID")

    # update
    p_update = sub.add_parser("update", help="更新任务状态")
    p_update.add_argument("task_id", help="任务 ID")
    p_update.add_argument("status", help="新状态")
    p_update.add_argument("--result", help="结果 JSON")
    p_update.add_argument("--note", help="状态变更备注")

    # files
    p_files = sub.add_parser("files", help="查看任务文件列表")
    p_files.add_argument("task_id", help="任务 ID")

    # timeline
    p_tl = sub.add_parser("timeline", help="查看任务时间线")
    p_tl.add_argument("task_id", help="任务 ID")

    # note
    p_note = sub.add_parser("note", help="添加备注")
    p_note.add_argument("task_id", help="任务 ID")
    p_note.add_argument("note_text", help="备注内容")

    args = parser.parse_args()
    if args.command == "list":
        list_tasks(args)
    elif args.command == "show":
        show_task(args)
    elif args.command == "update":
        update_status(args)
    elif args.command == "files":
        list_files(args)
    elif args.command == "timeline":
        timeline(args)
    elif args.command == "note":
        add_note(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
