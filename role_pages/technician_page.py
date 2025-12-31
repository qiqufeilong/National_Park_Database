import tkinter as tk
from tkinter import scrolledtext, messagebox
import db_utils
import pymysql
import datetime

def open(user_id, real_name):
    window = tk.Tk()
    window.title(f"技术人员-{real_name}")
    window.geometry("900x700")

    # 布局：左侧功能区，右侧结果区
    left_frame = tk.Frame(window)
    left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="n")
    right_frame = tk.Frame(window)
    right_frame.grid(row=0, column=1, padx=20, pady=20)

    # 结果显示区
    scroll_text = scrolledtext.ScrolledText(right_frame, width=70, height=40)
    scroll_text.pack()

    # ========== 功能1：维护监测设备 ==========
    tk.Label(left_frame, text="维护监测设备", font=("黑体", 12)).grid(row=0, column=0, columnspan=2, pady=10)
    tk.Label(left_frame, text="设备编号：").grid(row=1, column=0, sticky="w")
    entry_device_id = tk.Entry(left_frame, width=20)
    entry_device_id.grid(row=1, column=1)
    tk.Label(left_frame, text="运行状态：").grid(row=2, column=0, sticky="w")
    entry_status = tk.Entry(left_frame, width=20, value="正常")
    entry_status.grid(row=2, column=1)
    tk.Label(left_frame, text="最后校准时间：").grid(row=3, column=0, sticky="w")
    entry_calibrate = tk.Entry(left_frame, width=20, value=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    entry_calibrate.grid(row=3, column=1)

    def maintain_device():
        device_id = entry_device_id.get().strip()
        run_status = entry_status.get().strip()
        last_calibrate = entry_calibrate.get().strip()

        if not all([device_id, run_status, last_calibrate]):
            messagebox.showwarning("警告", "请填写完整维护信息！")
            return

        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor()
        try:
            sql = """
            UPDATE np_monitor_device 
            SET run_status=%s, last_calibrate_time=%s 
            WHERE device_id=%s
            """
            cursor.execute(sql, (run_status, last_calibrate, device_id))
            if cursor.rowcount > 0:
                conn.commit()
                scroll_text.insert(tk.INSERT, f"设备{device_id}维护成功！状态：{run_status}，校准时间：{last_calibrate}\n")
            else:
                scroll_text.insert(tk.INSERT, f"维护失败！未找到设备{device_id}\n")
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"维护失败：{e}\n")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="提交维护记录", command=maintain_device, width=15).grid(row=4, column=0, columnspan=2, pady=5)

    # ========== 功能2：处理设备故障报修 ==========
    tk.Label(left_frame, text="处理故障报修", font=("黑体", 12)).grid(row=5, column=0, columnspan=2, pady=10)
    tk.Label(left_frame, text="设备编号：").grid(row=6, column=0, sticky="w")
    entry_device_id2 = tk.Entry(left_frame, width=20)
    entry_device_id2.grid(row=6, column=1)
    tk.Label(left_frame, text="故障描述：").grid(row=7, column=0, sticky="w")
    entry_fault = tk.Entry(left_frame, width=20)
    entry_fault.grid(row=7, column=1)
    tk.Label(left_frame, text="处理结果：").grid(row=8, column=0, sticky="w")
    entry_result = tk.Entry(left_frame, width=20, value="已修复")
    entry_result.grid(row=8, column=1)

    def handle_fault():
        device_id = entry_device_id2.get().strip()
        fault_desc = entry_fault.get().strip()
        handle_result = entry_result.get().strip()

        if not all([device_id, fault_desc, handle_result]):
            messagebox.showwarning("警告", "请填写完整故障信息！")
            return

        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor()
        try:
            # 更新设备状态（已修复则改为正常，否则故障）
            run_status = "正常" if handle_result == "已修复" else "故障"
            sql = """
            UPDATE np_monitor_device 
            SET run_status=%s 
            WHERE device_id=%s
            """
            cursor.execute(sql, (run_status, device_id))
            
            # 记录故障处理（可扩展故障表，此处简化）
            scroll_text.insert(tk.INSERT, f"设备{device_id}故障处理完成！\n")
            scroll_text.insert(tk.INSERT, f"故障描述：{fault_desc} | 处理结果：{handle_result} | 设备状态：{run_status}\n")
            
            conn.commit()
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"处理故障失败：{e}\n")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="提交处理结果", command=handle_fault, width=15).grid(row=9, column=0, columnspan=2, pady=5)

    # ========== 功能3：查看设备运行状态 ==========
    def view_device_status():
        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            sql = """
            SELECT d.*, a.area_name 
            FROM np_monitor_device d
            JOIN np_area a ON d.deploy_area_id = a.area_id
            ORDER BY d.run_status
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            scroll_text.insert(tk.INSERT, f"【所有监测设备状态】共{len(results)}台\n")
            scroll_text.insert(tk.INSERT, "="*80 + "\n")
            
            # 统计状态
            status_count = {}
            for res in results:
                status = res['run_status']
                status_count[status] = status_count.get(status, 0) + 1
            
            scroll_text.insert(tk.INSERT, "■ 状态统计：\n")
            for status, count in status_count.items():
                scroll_text.insert(tk.INSERT, f"  {status}：{count} 台\n")
            
            scroll_text.insert(tk.INSERT, "\n■ 设备详情：\n")
            for res in results:
                scroll_text.insert(tk.INSERT, f"""
                设备编号：{res['device_id']} | 类型：{res['device_type']}
                部署区域：{res['area_name']} | 状态：{res['run_status']}
                安装时间：{res['install_time']} | 校准周期：{res['calibrate_cycle']}
                最后校准：{res['last_calibrate_time'] or '未校准'}
                -------------------------\n
                """)
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"查询设备失败：{e}\n")
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="查看设备状态", command=view_device_status, width=15).grid(row=10, column=0, columnspan=2, pady=5)

    # ========== 功能4：优化数据采集策略 ==========
    tk.Label(left_frame, text="优化采集策略", font=("黑体", 12)).grid(row=11, column=0, columnspan=2, pady=10)
    tk.Label(left_frame, text="指标编号：").grid(row=12, column=0, sticky="w")
    entry_index_id = tk.Entry(left_frame, width=20)
    entry_index_id.grid(row=12, column=1)
    tk.Label(left_frame, text="监测频率：").grid(row=13, column=0, sticky="w")
    entry_frequency = tk.Entry(left_frame, width=20, value="小时")
    entry_frequency.grid(row=13, column=1)

    def optimize_collect():
        index_id = entry_index_id.get().strip()
        frequency = entry_frequency.get().strip()
        if not index_id or not frequency:
            messagebox.showwarning("警告", "请填写完整优化信息！")
            return

        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor()
        try:
            sql = """
            UPDATE np_env_index 
            SET monitor_frequency=%s 
            WHERE index_id=%s
            """
            cursor.execute(sql, (frequency, index_id))
            if cursor.rowcount > 0:
                conn.commit()
                scroll_text.insert(tk.INSERT, f"指标{index_id}采集策略优化成功！监测频率：{frequency}\n")
            else:
                scroll_text.insert(tk.INSERT, f"优化失败！未找到指标{index_id}\n")
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"优化失败：{e}\n")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="提交优化配置", command=optimize_collect, width=15).grid(row=14, column=0, columnspan=2, pady=5)

    # ========== 功能5：查看设备校准提醒 ==========
    def view_calibrate_remind():
        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            # 查询近7天需要校准的设备
            cursor.execute("""
            SELECT d.device_id, d.device_type, a.area_name, d.calibrate_cycle, d.last_calibrate_time 
            FROM np_monitor_device d
            JOIN np_area a ON d.deploy_area_id = a.area_id
            WHERE d.run_status='正常' 
            AND (d.last_calibrate_time IS NULL OR d.last_calibrate_time <= DATE_SUB(NOW(), INTERVAL 7 DAY))
            """)
            results = cursor.fetchall()
            scroll_text.insert(tk.INSERT, f"【设备校准提醒（近7天）】共{len(results)}台\n")
            scroll_text.insert(tk.INSERT, "="*80 + "\n")
            if not results:
                scroll_text.insert(tk.INSERT, "暂无需要校准的设备\n")
                return

            for res in results:
                scroll_text.insert(tk.INSERT, f"""
                设备编号：{res['device_id']} | 类型：{res['device_type']}
                部署区域：{res['area_name']} | 校准周期：{res['calibrate_cycle']}
                最后校准：{res['last_calibrate_time'] or '从未校准'}
                -------------------------\n
                """)
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"查询校准提醒失败：{e}\n")
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="查看校准提醒", command=view_calibrate_remind, width=15).grid(row=15, column=0, columnspan=2, pady=5)

    # ========== 退出按钮 ==========
    tk.Button(left_frame, text="退出", command=window.destroy, width=15, bg="#ff4444", fg="white").grid(row=16, column=0, columnspan=2, pady=20)

    window.mainloop()