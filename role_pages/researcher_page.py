import tkinter as tk
from tkinter import scrolledtext, messagebox
import db_utils
import pymysql
import datetime

def open(user_id, real_name):
    window = tk.Tk()
    window.title(f"科研人员-{real_name}")
    window.geometry("900x700")

    # 布局：左侧功能区，右侧结果区
    left_frame = tk.Frame(window)
    left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="n")
    right_frame = tk.Frame(window)
    right_frame.grid(row=0, column=1, padx=20, pady=20)

    # 结果显示区
    scroll_text = scrolledtext.ScrolledText(right_frame, width=70, height=40)
    scroll_text.pack()

    # ========== 功能1：提交科研项目申请 ==========
    tk.Label(left_frame, text="提交科研项目申请", font=("黑体", 12)).grid(row=0, column=0, columnspan=2, pady=10)
    tk.Label(left_frame, text="项目名称：").grid(row=1, column=0, sticky="w")
    entry_proj_name = tk.Entry(left_frame, width=20)
    entry_proj_name.grid(row=1, column=1)
    tk.Label(left_frame, text="申请单位：").grid(row=2, column=0, sticky="w")
    entry_unit = tk.Entry(left_frame, width=20)
    entry_unit.grid(row=2, column=1)
    tk.Label(left_frame, text="研究领域：").grid(row=3, column=0, sticky="w")
    entry_field = tk.Entry(left_frame, width=20)
    entry_field.grid(row=3, column=1)
    tk.Label(left_frame, text="结题时间：").grid(row=4, column=0, sticky="w")
    entry_finish = tk.Entry(left_frame, width=20, value=(datetime.date.today() + datetime.timedelta(days=365)).strftime("%Y-%m-%d"))
    entry_finish.grid(row=4, column=1)

    def submit_project():
        proj_name = entry_proj_name.get().strip()
        apply_unit = entry_unit.get().strip()
        research_field = entry_field.get().strip()
        finish_time = entry_finish.get().strip()

        if not all([proj_name, apply_unit, research_field, finish_time]):
            messagebox.showwarning("警告", "请填写完整项目信息！")
            return

        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor()
        project_id = f"RP{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        try:
            sql = """
            INSERT INTO np_research_project 
            (project_id, project_name, leader_id, apply_unit, approve_time, finish_time, project_status, research_field, data_permission)
            VALUES (%s, %s, %s, %s, NOW(), %s, '在研', %s, '内部共享')
            """
            cursor.execute(sql, (project_id, proj_name, user_id, apply_unit, finish_time, research_field))
            conn.commit()
            scroll_text.insert(tk.INSERT, f"项目申请提交成功！项目编号：{project_id}\n")
            scroll_text.insert(tk.INSERT, f"项目名称：{proj_name} | 研究领域：{research_field}\n")
            scroll_text.insert(tk.INSERT, f"状态：待公园管理人员审批\n")
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"提交失败：{e}\n")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="提交申请", command=submit_project, width=15).grid(row=5, column=0, columnspan=2, pady=5)

    # ========== 功能2：录入科研数据采集记录 ==========
    tk.Label(left_frame, text="录入数据采集记录", font=("黑体", 12)).grid(row=6, column=0, columnspan=2, pady=10)
    tk.Label(left_frame, text="项目编号：").grid(row=7, column=0, sticky="w")
    entry_proj_id = tk.Entry(left_frame, width=20)
    entry_proj_id.grid(row=7, column=1)
    tk.Label(left_frame, text="采集区域：").grid(row=8, column=0, sticky="w")
    entry_area = tk.Entry(left_frame, width=20)
    entry_area.grid(row=8, column=1)
    tk.Label(left_frame, text="采集内容：").grid(row=9, column=0, sticky="w")
    entry_content = tk.Entry(left_frame, width=20)
    entry_content.grid(row=9, column=1)
    tk.Label(left_frame, text="数据来源：").grid(row=10, column=0, sticky="w")
    entry_source = tk.Entry(left_frame, width=20, value="实地采集")
    entry_source.grid(row=10, column=1)

    def add_collect_record():
        project_id = entry_proj_id.get().strip()
        area_id = entry_area.get().strip()
        collect_content = entry_content.get().strip()
        data_source = entry_source.get().strip()

        if not all([project_id, area_id, collect_content, data_source]):
            messagebox.showwarning("警告", "请填写完整采集信息！")
            return

        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor()
        collect_id = f"RC{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        try:
            # 校验项目是否存在且在研
            cursor.execute("SELECT project_status FROM np_research_project WHERE project_id=%s AND leader_id=%s", (project_id, user_id))
            proj = cursor.fetchone()
            if not proj or proj[0] != '在研':
                scroll_text.insert(tk.INSERT, "项目不存在或非在研状态！\n")
                return

            sql = """
            INSERT INTO np_research_collect 
            (collect_id, project_id, collector_id, collect_time, area_id, collect_content, data_source)
            VALUES (%s, %s, %s, NOW(), %s, %s, %s)
            """
            cursor.execute(sql, (collect_id, project_id, user_id, area_id, collect_content, data_source))
            conn.commit()
            scroll_text.insert(tk.INSERT, f"采集记录录入成功！采集编号：{collect_id}\n")
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"录入失败：{e}\n")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="录入记录", command=add_collect_record, width=15).grid(row=11, column=0, columnspan=2, pady=5)

    # ========== 功能3：上传科研成果 ==========
    tk.Label(left_frame, text="上传科研成果", font=("黑体", 12)).grid(row=12, column=0, columnspan=2, pady=10)
    tk.Label(left_frame, text="项目编号：").grid(row=13, column=0, sticky="w")
    entry_proj_id2 = tk.Entry(left_frame, width=20)
    entry_proj_id2.grid(row=13, column=1)
    tk.Label(left_frame, text="成果名称：").grid(row=14, column=0, sticky="w")
    entry_ach_name = tk.Entry(left_frame, width=20)
    entry_ach_name.grid(row=14, column=1)
    tk.Label(left_frame, text="成果类型：").grid(row=15, column=0, sticky="w")
    entry_ach_type = tk.Entry(left_frame, width=20, value="论文")
    entry_ach_type.grid(row=15, column=1)
    tk.Label(left_frame, text="共享权限：").grid(row=16, column=0, sticky="w")
    entry_permission = tk.Entry(left_frame, width=20, value="内部共享")
    entry_permission.grid(row=16, column=1)

    def upload_achievement():
        project_id = entry_proj_id2.get().strip()
        ach_name = entry_ach_name.get().strip()
        ach_type = entry_ach_type.get().strip()
        share_permission = entry_permission.get().strip()

        if not all([project_id, ach_name, ach_type, share_permission]):
            messagebox.showwarning("警告", "请填写完整成果信息！")
            return

        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor()
        achievement_id = f"RA{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        file_path = f"/upload/research/{achievement_id}.pdf"  # 模拟文件路径
        try:
            sql = """
            INSERT INTO np_research_achievement 
            (achievement_id, project_id, achievement_type, achievement_name, publish_time, share_permission, file_path)
            VALUES (%s, %s, %s, %s, NOW(), %s, %s)
            """
            cursor.execute(sql, (achievement_id, project_id, ach_type, ach_name, share_permission, file_path))
            conn.commit()
            scroll_text.insert(tk.INSERT, f"成果上传成功！成果编号：{achievement_id}\n")
            scroll_text.insert(tk.INSERT, f"文件路径：{file_path} | 共享权限：{share_permission}\n")
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"上传失败：{e}\n")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="上传成果", command=upload_achievement, width=15).grid(row=17, column=0, columnspan=2, pady=5)

    # ========== 功能4：查看我的项目 ==========
    def view_my_project():
        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            sql = """
            SELECT * FROM np_research_project WHERE leader_id=%s ORDER BY approve_time DESC
            """
            cursor.execute(sql, (user_id,))
            results = cursor.fetchall()
            scroll_text.insert(tk.INSERT, f"【我的科研项目】共{len(results)}条\n")
            scroll_text.insert(tk.INSERT, "="*80 + "\n")
            for res in results:
                scroll_text.insert(tk.INSERT, f"""
                项目编号：{res['project_id']} | 名称：{res['project_name']}
                申请单位：{res['apply_unit']} | 立项时间：{res['approve_time']}
                结题时间：{res['finish_time']} | 状态：{res['project_status']}
                研究领域：{res['research_field']} | 数据权限：{res['data_permission']}
                -------------------------\n
                """)
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"查询失败：{e}\n")
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="查看我的项目", command=view_my_project, width=15).grid(row=18, column=0, columnspan=2, pady=5)

    # ========== 退出按钮 ==========
    tk.Button(left_frame, text="退出", command=window.destroy, width=15, bg="#ff4444", fg="white").grid(row=19, column=0, columnspan=2, pady=20)

    window.mainloop()