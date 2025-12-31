import tkinter as tk
from tkinter import scrolledtext
import db_utils
import pymysql
import datetime

def open(user_id, real_name):
    window = tk.Tk()
    window.title(f"生态监测员-{real_name}")
    window.geometry("800x600")

    # 界面布局：左侧功能区，右侧结果区
    left_frame = tk.Frame(window)
    left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="n")
    right_frame = tk.Frame(window)
    right_frame.grid(row=0, column=1, padx=20, pady=20)

    # 功能1：上传监测记录
    tk.Label(left_frame, text="上传物种监测记录", font=("黑体", 12)).grid(row=0, column=0, pady=10)
    tk.Label(left_frame, text="物种编号：").grid(row=1, column=0, sticky="w")
    entry_sp_id = tk.Entry(left_frame, width=20)
    entry_sp_id.grid(row=1, column=1)
    tk.Label(left_frame, text="监测设备编号：").grid(row=2, column=0, sticky="w")
    entry_device_id = tk.Entry(left_frame, width=20)
    entry_device_id.grid(row=2, column=1)
    tk.Label(left_frame, text="监测时间：").grid(row=3, column=0, sticky="w")
    # 正确代码（去掉value，改用insert设置初始值）
    entry_time = tk.Entry(left_frame, width=20)                 
    # 设置默认的监测时间（当前时间）
    entry_time.insert(0, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    entry_time.grid(row=3, column=1)
    tk.Label(left_frame, text="监测经度：").grid(row=4, column=0, sticky="w")
    entry_lng = tk.Entry(left_frame, width=20)
    entry_lng.grid(row=4, column=1)
    tk.Label(left_frame, text="监测纬度：").grid(row=5, column=0, sticky="w")
    entry_lat = tk.Entry(left_frame, width=20)
    entry_lat.grid(row=5, column=1)
    tk.Label(left_frame, text="监测方式：").grid(row=6, column=0, sticky="w")
    entry_method = tk.Entry(left_frame, width=20)
    entry_method.grid(row=6, column=1)
    tk.Label(left_frame, text="监测内容：").grid(row=7, column=0, sticky="w")
    entry_content = tk.Entry(left_frame, width=20)
    entry_content.grid(row=7, column=1)

    # 结果显示区
    scrollbar = scrolledtext.ScrolledText(right_frame, width=60, height=30)
    scrollbar.pack()

    def upload_monitor():
        """上传监测记录"""
        sp_id = entry_sp_id.get().strip()
        device_id = entry_device_id.get().strip()
        monitor_time = entry_time.get().strip()
        lng = entry_lng.get().strip()
        lat = entry_lat.get().strip()
        method = entry_method.get().strip()
        content = entry_content.get().strip()

        if not all([sp_id, device_id, monitor_time, lng, lat, method, content]):
            scrollbar.insert(tk.INSERT, "请填写完整信息！\n")
            return

        conn = db_utils.get_db_conn()
        if not conn:
            scrollbar.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor()
        monitor_id = f"BM{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        try:
            sql = """
            INSERT INTO np_biodiversity_monitor 
            (monitor_id, sp_id, device_id, monitor_time, monitor_lng, monitor_lat, monitor_method, monitor_content, recorder_id, data_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, '待核实')
            """
            cursor.execute(sql, (monitor_id, sp_id, device_id, monitor_time, lng, lat, method, content, user_id))
            conn.commit()
            scrollbar.insert(tk.INSERT, f"上传成功！监测记录编号：{monitor_id}\n")
        except Exception as e:
            scrollbar.insert(tk.INSERT, f"上传失败：{e}\n")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    # 功能2：查询我的监测记录
    def query_my_monitor():
        """查询当前用户的监测记录"""
        conn = db_utils.get_db_conn()
        if not conn:
            scrollbar.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            sql = """
            SELECT m.*, s.sp_name_cn FROM np_biodiversity_monitor m
            JOIN np_species s ON m.sp_id = s.sp_id
            WHERE m.recorder_id = %s
            ORDER BY m.monitor_time DESC
            """
            cursor.execute(sql, (user_id,))
            results = cursor.fetchall()
            scrollbar.insert(tk.INSERT, f"我的监测记录（共{len(results)}条）：\n")
            for res in results:
                scrollbar.insert(tk.INSERT, f"""
                记录编号：{res['monitor_id']}
                物种名称：{res['sp_name_cn']}
                监测时间：{res['monitor_time']}
                监测地点：{res['monitor_lng']},{res['monitor_lat']}
                状态：{res['data_status']}
                -------------------------\n
                """)
        except Exception as e:
            scrollbar.insert(tk.INSERT, f"查询失败：{e}\n")
        finally:
            cursor.close()
            conn.close()

    # 按钮
    tk.Button(left_frame, text="上传记录", command=upload_monitor, width=15).grid(row=8, column=0, pady=10)
    tk.Button(left_frame, text="查询我的记录", command=query_my_monitor, width=15).grid(row=8, column=1, pady=10)
    tk.Button(left_frame, text="退出", command=window.destroy, width=15).grid(row=9, column=0, columnspan=2, pady=10)

    window.mainloop()