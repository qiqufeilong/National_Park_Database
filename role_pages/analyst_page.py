import tkinter as tk
from tkinter import scrolledtext, ttk
import db_utils
import datetime
import pymysql

def open(user_id, real_name):
    window = tk.Tk()
    window.title(f"数据分析师-{real_name}")
    window.geometry("900x700")

    # 布局：左侧功能区，右侧结果区
    left_frame = tk.Frame(window)
    left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="n")
    right_frame = tk.Frame(window)
    right_frame.grid(row=0, column=1, padx=20, pady=20)

    # 结果显示区
    scroll_text = scrolledtext.ScrolledText(right_frame, width=70, height=40)
    scroll_text.pack()

    # ========== 功能1：审核生物监测数据 ==========
    tk.Label(left_frame, text="审核生物监测数据", font=("黑体", 12)).grid(row=0, column=0, columnspan=2, pady=10)
    tk.Label(left_frame, text="监测记录编号：").grid(row=1, column=0, sticky="w")
    entry_monitor_id = tk.Entry(left_frame, width=20)
    entry_monitor_id.grid(row=1, column=1)
    tk.Label(left_frame, text="审核结论：").grid(row=2, column=0, sticky="w")
    entry_audit = tk.Entry(left_frame, width=20)
    entry_audit.grid(row=2, column=1)

    def audit_monitor_data():
        monitor_id = entry_monitor_id.get().strip()
        audit_result = entry_audit.get().strip()
        if not monitor_id or not audit_result:
            scroll_text.insert(tk.INSERT, "请填写完整审核信息！\n")
            return

        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor()
        try:
            sql = """
            UPDATE np_biodiversity_monitor 
            SET data_status='有效', audit_user_id=%s, audit_result=%s, audit_time=NOW()
            WHERE monitor_id=%s
            """
            cursor.execute(sql, (user_id, audit_result, monitor_id))
            if cursor.rowcount > 0:
                conn.commit()
                scroll_text.insert(tk.INSERT, f"审核成功！记录{monitor_id}已标记为有效\n")
            else:
                scroll_text.insert(tk.INSERT, f"审核失败！未找到记录{monitor_id}\n")
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"审核失败：{e}\n")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="提交审核", command=audit_monitor_data, width=15).grid(row=3, column=0, columnspan=2, pady=5)

    # ========== 功能2：生成环境异常报告 ==========
    def gen_env_warn_report():
        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            # 查询近24小时环境异常数据
            sql = """
            SELECT e.*, i.index_name, a.area_name, d.device_type 
            FROM np_env_monitor e
            JOIN np_env_index i ON e.index_id = i.index_id
            JOIN np_area a ON e.area_id = a.area_id
            JOIN np_monitor_device d ON e.device_id = d.device_id
            WHERE e.is_abnormal=1 AND e.collect_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            ORDER BY e.collect_time DESC
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            scroll_text.insert(tk.INSERT, f"【近24小时环境异常报告】{datetime.datetime.now()}\n")
            scroll_text.insert(tk.INSERT, "="*80 + "\n")
            if not results:
                scroll_text.insert(tk.INSERT, "暂无异常数据\n")
                return

            for res in results:
                scroll_text.insert(tk.INSERT, f"""
                区域：{res['area_name']} | 指标：{res['index_name']} | 监测值：{res['monitor_value']}
                阈值范围：{res['threshold_lower']}-{res['threshold_upper']} | 设备：{res['device_type']}
                采集时间：{res['collect_time']} | 数据质量：{res['data_quality']}
                -------------------------\n
                """)
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"生成报告失败：{e}\n")
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="生成环境异常报告", command=gen_env_warn_report, width=15).grid(row=4, column=0, columnspan=2, pady=5)

    # ========== 功能3：查询物种监测趋势 ==========
    tk.Label(left_frame, text="查询物种监测趋势", font=("黑体", 12)).grid(row=5, column=0, columnspan=2, pady=10)
    tk.Label(left_frame, text="物种编号：").grid(row=6, column=0, sticky="w")
    entry_sp_id = tk.Entry(left_frame, width=20)
    entry_sp_id.grid(row=6, column=1)

    def query_sp_trend():
        sp_id = entry_sp_id.get().strip()
        if not sp_id:
            scroll_text.insert(tk.INSERT, "请填写物种编号！\n")
            return

        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            # 查询近7天该物种的监测次数
            sql = """
            SELECT DATE(monitor_time) AS monitor_date, COUNT(*) AS monitor_count
            FROM np_biodiversity_monitor
            WHERE sp_id=%s AND monitor_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(monitor_time)
            ORDER BY monitor_date
            """
            cursor.execute(sql, (sp_id,))
            results = cursor.fetchall()

            # 查询物种名称
            cursor.execute("SELECT sp_name_cn FROM np_species WHERE sp_id=%s", (sp_id,))
            sp_name = cursor.fetchone()
            if not sp_name:
                scroll_text.insert(tk.INSERT, f"未找到物种{sp_id}！\n")
                return

            scroll_text.insert(tk.INSERT, f"【{sp_name['sp_name_cn']}近7天监测趋势】\n")
            scroll_text.insert(tk.INSERT, "日期         | 监测次数\n")
            scroll_text.insert(tk.INSERT, "------------------------\n")
            for res in results:
                scroll_text.insert(tk.INSERT, f"{res['monitor_date']} | {res['monitor_count']}\n")
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"查询趋势失败：{e}\n")
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="查询趋势", command=query_sp_trend, width=15).grid(row=7, column=0, columnspan=2, pady=5)

    # ========== 退出按钮 ==========
    tk.Button(left_frame, text="退出", command=window.destroy, width=15, bg="#ff4444", fg="white").grid(row=8, column=0, columnspan=2, pady=20)

    window.mainloop()