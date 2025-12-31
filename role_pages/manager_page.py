import tkinter as tk
from tkinter import scrolledtext, messagebox
import db_utils
import pymysql
import datetime

def open(user_id, real_name):
    window = tk.Tk()
    window.title(f"公园管理人员-{real_name}")
    window.geometry("1000x700")

    # 布局：左侧功能区，右侧结果区
    left_frame = tk.Frame(window)
    left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="n")
    right_frame = tk.Frame(window)
    right_frame.grid(row=0, column=1, padx=20, pady=20)

    # 结果显示区
    scroll_text = scrolledtext.ScrolledText(right_frame, width=80, height=40)
    scroll_text.pack()

    # ========== 功能1：查看全系统业务汇总 ==========
    def view_business_summary():
        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            scroll_text.insert(tk.INSERT, f"【全系统业务汇总】{datetime.datetime.now()}\n")
            scroll_text.insert(tk.INSERT, "="*100 + "\n")

            # 1. 流量汇总
            cursor.execute("""
            SELECT a.area_name, f.real_time_people, f.max_capacity, f.current_status 
            FROM np_flow_control f
            JOIN np_area a ON f.area_id = a.area_id
            """)
            flow_res = cursor.fetchall()
            scroll_text.insert(tk.INSERT, "■ 区域流量状态：\n")
            for res in flow_res:
                scroll_text.insert(tk.INSERT, f"  {res['area_name']}：{res['real_time_people']}/{res['max_capacity']} 人 | 状态：{res['current_status']}\n")

            # 2. 非法行为汇总
            cursor.execute("""
            SELECT handle_status, COUNT(*) AS count 
            FROM np_illegal_behavior 
            GROUP BY handle_status
            """)
            illegal_res = cursor.fetchall()
            scroll_text.insert(tk.INSERT, "\n■ 非法行为处理状态：\n")
            for res in illegal_res:
                scroll_text.insert(tk.INSERT, f"  {res['handle_status']}：{res['count']} 条\n")

            # 3. 科研项目汇总
            cursor.execute("""
            SELECT project_status, COUNT(*) AS count 
            FROM np_research_project 
            GROUP BY project_status
            """)
            proj_res = cursor.fetchall()
            scroll_text.insert(tk.INSERT, "\n■ 科研项目状态：\n")
            for res in proj_res:
                scroll_text.insert(tk.INSERT, f"  {res['project_status']}：{res['count']} 个\n")

            # 4. 环境异常汇总
            cursor.execute("SELECT COUNT(*) AS count FROM np_env_monitor WHERE is_abnormal=1 AND collect_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)")
            env_res = cursor.fetchone()
            scroll_text.insert(tk.INSERT, f"\n■ 近24小时环境异常数据：{env_res['count']} 条\n")

            scroll_text.insert(tk.INSERT, "="*100 + "\n")
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"查询汇总失败：{e}\n")
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="查看业务汇总", command=view_business_summary, width=20).grid(row=0, column=0, pady=10)

    # ========== 功能2：审批科研项目 ==========
    tk.Label(left_frame, text="审批科研项目", font=("黑体", 12)).grid(row=1, column=0, columnspan=2, pady=10)
    tk.Label(left_frame, text="项目编号：").grid(row=2, column=0, sticky="w")
    entry_proj_id = tk.Entry(left_frame, width=20)
    entry_proj_id.grid(row=2, column=1)
    tk.Label(left_frame, text="审批结果：").grid(row=3, column=0, sticky="w")
    entry_approve = tk.Entry(left_frame, width=20, value="通过")
    entry_approve.grid(row=3, column=1)

    def approve_project():
        project_id = entry_proj_id.get().strip()
        approve_result = entry_approve.get().strip()
        if not project_id or not approve_result:
            messagebox.showwarning("警告", "请填写完整审批信息！")
            return

        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor()
        try:
            # 更新项目状态（通过/驳回）
            status = "在研" if approve_result == "通过" else "暂停"
            sql = """
            UPDATE np_research_project 
            SET project_status=%s 
            WHERE project_id=%s
            """
            cursor.execute(sql, (status, project_id))
            if cursor.rowcount > 0:
                conn.commit()
                scroll_text.insert(tk.INSERT, f"项目{project_id}审批完成！结果：{approve_result}，状态：{status}\n")
            else:
                scroll_text.insert(tk.INSERT, f"审批失败！未找到项目{project_id}\n")
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"审批失败：{e}\n")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="提交审批", command=approve_project, width=20).grid(row=4, column=0, columnspan=2, pady=5)

    # ========== 功能3：配置流量控制策略 ==========
    tk.Label(left_frame, text="配置流量策略", font=("黑体", 12)).grid(row=5, column=0, columnspan=2, pady=10)
    tk.Label(left_frame, text="区域编号：").grid(row=6, column=0, sticky="w")
    entry_area_id = tk.Entry(left_frame, width=20)
    entry_area_id.grid(row=6, column=1)
    tk.Label(left_frame, text="预警阈值：").grid(row=7, column=0, sticky="w")
    entry_threshold = tk.Entry(left_frame, width=20)
    entry_threshold.grid(row=7, column=1)

    def config_flow():
        area_id = entry_area_id.get().strip()
        threshold = entry_threshold.get().strip()
        if not area_id or not threshold:
            messagebox.showwarning("警告", "请填写完整配置信息！")
            return

        try:
            threshold = int(threshold)
            if threshold < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("警告", "预警阈值必须为正整数！")
            return

        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor()
        try:
            # 更新流量预警阈值
            sql = """
            UPDATE np_flow_control 
            SET warn_threshold=%s, update_time=NOW()
            WHERE area_id=%s
            """
            cursor.execute(sql, (threshold, area_id))
            if cursor.rowcount > 0:
                conn.commit()
                scroll_text.insert(tk.INSERT, f"区域{area_id}流量策略配置成功！预警阈值：{threshold}\n")
            else:
                # 无记录则新增
                flow_id = f"FC{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                sql2 = """
                INSERT INTO np_flow_control 
                (flow_id, area_id, real_time_people, warn_threshold, current_status)
                VALUES (%s, %s, 0, %s, '正常')
                """
                cursor.execute(sql2, (flow_id, area_id, threshold))
                conn.commit()
                scroll_text.insert(tk.INSERT, f"区域{area_id}流量策略创建成功！预警阈值：{threshold}\n")
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"配置失败：{e}\n")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="配置阈值", command=config_flow, width=20).grid(row=8, column=0, columnspan=2, pady=5)

    # ========== 功能4：查看预警信息 ==========
    def view_warning():
        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            scroll_text.insert(tk.INSERT, f"【系统预警信息】{datetime.datetime.now()}\n")
            scroll_text.insert(tk.INSERT, "="*80 + "\n")

            # 1. 流量预警
            cursor.execute("""
            SELECT a.area_name, f.real_time_people, f.warn_threshold 
            FROM np_flow_control f
            JOIN np_area a ON f.area_id = a.area_id
            WHERE f.current_status='预警'
            """)
            flow_warn = cursor.fetchall()
            if flow_warn:
                scroll_text.insert(tk.INSERT, "■ 流量预警：\n")
                for res in flow_warn:
                    scroll_text.insert(tk.INSERT, f"  {res['area_name']}：{res['real_time_people']} 人（阈值{res['warn_threshold']}）\n")
            else:
                scroll_text.insert(tk.INSERT, "■ 流量预警：无\n")

            # 2. 环境异常预警
            cursor.execute("""
            SELECT a.area_name, i.index_name, e.monitor_value, e.collect_time 
            FROM np_env_monitor e
            JOIN np_area a ON e.area_id = a.area_id
            JOIN np_env_index i ON e.index_id = i.index_id
            WHERE e.is_abnormal=1 AND e.collect_time >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
            """)
            env_warn = cursor.fetchall()
            if env_warn:
                scroll_text.insert(tk.INSERT, "\n■ 环境异常预警（近1小时）：\n")
                for res in env_warn:
                    scroll_text.insert(tk.INSERT, f"  {res['area_name']} | {res['index_name']}：{res['monitor_value']} | 时间：{res['collect_time']}\n")
            else:
                scroll_text.insert(tk.INSERT, "\n■ 环境异常预警：无\n")

            # 3. 非法行为预警
            cursor.execute("""
            SELECT a.area_name, i.behavior_type, i.occur_time 
            FROM np_illegal_behavior i
            JOIN np_area a ON i.area_id = a.area_id
            WHERE i.handle_status='未处理'
            """)
            illegal_warn = cursor.fetchall()
            if illegal_warn:
                scroll_text.insert(tk.INSERT, "\n■ 未处理非法行为预警：\n")
                for res in illegal_warn:
                    scroll_text.insert(tk.INSERT, f"  {res['area_name']} | {res['behavior_type']} | 时间：{res['occur_time']}\n")
            else:
                scroll_text.insert(tk.INSERT, "\n■ 未处理非法行为预警：无\n")

            scroll_text.insert(tk.INSERT, "="*80 + "\n")
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"查询预警失败：{e}\n")
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="查看预警信息", command=view_warning, width=20).grid(row=9, column=0, columnspan=2, pady=5)

    # ========== 退出按钮 ==========
    tk.Button(left_frame, text="退出", command=window.destroy, width=20, bg="#ff4444", fg="white").grid(row=10, column=0, columnspan=2, pady=20)

    window.mainloop()