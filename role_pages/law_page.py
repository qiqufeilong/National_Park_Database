import tkinter as tk
from tkinter import scrolledtext, messagebox
import db_utils
import pymysql
import datetime

def open(user_id, real_name):
    window = tk.Tk()
    window.title(f"执法人员-{real_name}")
    window.geometry("900x700")

    # 布局
    left_frame = tk.Frame(window)
    left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="n")
    right_frame = tk.Frame(window)
    right_frame.grid(row=0, column=1, padx=20, pady=20)

    # 结果区
    scroll_text = scrolledtext.ScrolledText(right_frame, width=70, height=40)
    scroll_text.pack()

    # ========== 功能1：查看未处理非法行为 ==========
    def view_illegal():
        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            sql = """
            SELECT i.*, a.area_name, p.point_id 
            FROM np_illegal_behavior i
            JOIN np_area a ON i.area_id = a.area_id
            LEFT JOIN np_monitor_point p ON i.monitor_point_id = p.point_id
            WHERE i.handle_status='未处理' AND i.area_id IN (SELECT area_id FROM np_user WHERE user_id=%s)
            ORDER BY i.occur_time DESC
            """
            cursor.execute(sql, (user_id,))
            results = cursor.fetchall()
            scroll_text.insert(tk.INSERT, f"【未处理非法行为】{datetime.datetime.now()}\n")
            scroll_text.insert(tk.INSERT, "="*80 + "\n")
            if not results:
                scroll_text.insert(tk.INSERT, "暂无未处理非法行为\n")
                return

            for res in results:
                scroll_text.insert(tk.INSERT, f"""
                记录编号：{res['illegal_id']} | 行为类型：{res['behavior_type']}
                发生区域：{res['area_name']} | 发生时间：{res['occur_time']}
                证据路径：{res['evidence_path']} | 监控点：{res['point_id'] or '无'}
                -------------------------\n
                """)
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"查询失败：{e}\n")
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="查看未处理案件", command=view_illegal, width=20).grid(row=0, column=0, pady=10)

    # ========== 功能2：处理非法行为 ==========
    tk.Label(left_frame, text="处理非法行为", font=("黑体", 12)).grid(row=1, column=0, columnspan=2, pady=10)
    tk.Label(left_frame, text="案件编号：").grid(row=2, column=0, sticky="w")
    entry_illegal_id = tk.Entry(left_frame, width=20)
    entry_illegal_id.grid(row=2, column=1)
    tk.Label(left_frame, text="处理结果：").grid(row=3, column=0, sticky="w")
    entry_result = tk.Entry(left_frame, width=20)
    entry_result.grid(row=3, column=1)
    tk.Label(left_frame, text="处罚依据：").grid(row=4, column=0, sticky="w")
    entry_basis = tk.Entry(left_frame, width=20)
    entry_basis.grid(row=4, column=1)

    def handle_illegal():
        illegal_id = entry_illegal_id.get().strip()
        handle_result = entry_result.get().strip()
        punishment_basis = entry_basis.get().strip()
        if not all([illegal_id, handle_result, punishment_basis]):
            messagebox.showwarning("警告", "请填写完整处理信息！")
            return

        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor()
        try:
            # 更新非法行为状态
            sql1 = """
            UPDATE np_illegal_behavior 
            SET handle_status='已结案', law_id=%s, handle_result=%s, punishment_basis=%s
            WHERE illegal_id=%s
            """
            cursor.execute(sql1, (user_id, handle_result, punishment_basis, illegal_id))

            # 生成执法调度记录
            dispatch_id = f"LD{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            sql2 = """
            INSERT INTO np_law_dispatch 
            (dispatch_id, illegal_id, law_id, dispatch_time, finish_time, dispatch_status)
            VALUES (%s, %s, %s, NOW(), NOW(), '已完成')
            """
            cursor.execute(sql2, (dispatch_id, illegal_id, user_id))

            conn.commit()
            scroll_text.insert(tk.INSERT, f"处理成功！案件{illegal_id}已结案，调度编号：{dispatch_id}\n")
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"处理失败：{e}\n")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="提交处理结果", command=handle_illegal, width=20).grid(row=5, column=0, columnspan=2, pady=5)

    # ========== 功能3：查看我的执法记录 ==========
    def view_my_law():
        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            sql = """
            SELECT d.*, i.behavior_type, i.handle_result 
            FROM np_law_dispatch d
            JOIN np_illegal_behavior i ON d.illegal_id = i.illegal_id
            WHERE d.law_id=%s
            ORDER BY d.dispatch_time DESC
            """
            cursor.execute(sql, (user_id,))
            results = cursor.fetchall()
            scroll_text.insert(tk.INSERT, f"【我的执法记录】共{len(results)}条\n")
            scroll_text.insert(tk.INSERT, "="*80 + "\n")
            for res in results:
                scroll_text.insert(tk.INSERT, f"""
                调度编号：{res['dispatch_id']} | 案件类型：{res['behavior_type']}
                调度时间：{res['dispatch_time']} | 完成时间：{res['finish_time']}
                处理结果：{res['handle_result']} | 状态：{res['dispatch_status']}
                -------------------------\n
                """)
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"查询失败：{e}\n")
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="查看我的执法记录", command=view_my_law, width=20).grid(row=6, column=0, columnspan=2, pady=5)

    # ========== 退出按钮 ==========
    tk.Button(left_frame, text="退出", command=window.destroy, width=20, bg="#ff4444", fg="white").grid(row=7, column=0, columnspan=2, pady=20)

    window.mainloop()