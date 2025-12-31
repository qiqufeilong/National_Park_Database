import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import db_utils
import pymysql
import datetime

def open(user_id, real_name):
    window = tk.Tk()
    window.title(f"系统管理员-{real_name}")
    window.geometry("1000x700")

    # 布局
    left_frame = tk.Frame(window)
    left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="n")
    right_frame = tk.Frame(window)
    right_frame.grid(row=0, column=1, padx=20, pady=20)

    # 结果区
    scroll_text = scrolledtext.ScrolledText(right_frame, width=80, height=40)
    scroll_text.pack()

    # ========== 功能1：用户管理 - 添加用户 ==========
    tk.Label(left_frame, text="用户管理", font=("黑体", 12)).grid(row=0, column=0, columnspan=2, pady=10)
    tk.Label(left_frame, text="账号：").grid(row=1, column=0, sticky="w")
    entry_account = tk.Entry(left_frame, width=20)
    entry_account.grid(row=1, column=1)
    tk.Label(left_frame, text="密码：").grid(row=2, column=0, sticky="w")
    entry_pwd = tk.Entry(left_frame, width=20, show="*")
    entry_pwd.grid(row=2, column=1)
    tk.Label(left_frame, text="姓名：").grid(row=3, column=0, sticky="w")
    entry_name = tk.Entry(left_frame, width=20)
    entry_name.grid(row=3, column=1)
    tk.Label(left_frame, text="角色：").grid(row=4, column=0, sticky="w")
    combo_role = ttk.Combobox(left_frame, width=18, values=["monitor", "analyst", "tourist", "law", "admin"])
    combo_role.grid(row=4, column=1)
    combo_role.current(0)

    def add_user():
        account = entry_account.get().strip()
        pwd = entry_pwd.get().strip()
        name = entry_name.get().strip()
        role = combo_role.get()

        if not all([account, pwd, name, role]):
            messagebox.showwarning("警告", "请填写完整用户信息！")
            return

        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor()
        user_id = f"U{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        try:
            sql = """
            INSERT INTO np_user 
            (user_id, user_account, user_pwd, role_type, real_name, status)
            VALUES (%s, %s, %s, %s, %s, 1)
            """
            cursor.execute(sql, (user_id, account, db_utils.encrypt_pwd(pwd), role, name))
            conn.commit()
            scroll_text.insert(tk.INSERT, f"添加用户成功！用户ID：{user_id}\n")
            scroll_text.insert(tk.INSERT, f"账号：{account} | 角色：{role} | 姓名：{name}\n")
        except pymysql.IntegrityError:
            scroll_text.insert(tk.INSERT, f"添加失败！账号{account}已存在\n")
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"添加失败：{e}\n")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="添加用户", command=add_user, width=15).grid(row=5, column=0, columnspan=2, pady=5)

    # ========== 功能2：查看所有用户 ==========
    def view_all_user():
        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            sql = "SELECT user_id, user_account, real_name, role_type, status FROM np_user ORDER BY role_type"
            cursor.execute(sql)
            results = cursor.fetchall()
            scroll_text.insert(tk.INSERT, f"【所有用户】共{len(results)}条\n")
            scroll_text.insert(tk.INSERT, "ID       | 账号       | 姓名   | 角色       | 状态\n")
            scroll_text.insert(tk.INSERT, "="*60 + "\n")
            for res in results:
                status = "正常" if res['status'] == 1 else "禁用"
                scroll_text.insert(tk.INSERT, f"{res['user_id']} | {res['user_account']} | {res['real_name']} | {res['role_type']} | {status}\n")
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"查询用户失败：{e}\n")
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="查看所有用户", command=view_all_user, width=15).grid(row=6, column=0, columnspan=2, pady=5)

    # ========== 功能3：查看全园区流量 ==========
    def view_all_flow():
        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            sql = """
            SELECT f.*, a.area_name, a.max_capacity 
            FROM np_flow_control f
            JOIN np_area a ON f.area_id = a.area_id
            ORDER BY f.current_status DESC
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            scroll_text.insert(tk.INSERT, f"【全园区流量状态】{datetime.datetime.now()}\n")
            scroll_text.insert(tk.INSERT, "="*80 + "\n")
            for res in results:
                scroll_text.insert(tk.INSERT, f"""
                区域：{res['area_name']} | 实时人数：{res['real_time_people']}/{res['max_capacity']}
                预警阈值：{res['warn_threshold']} | 当前状态：{res['current_status']}
                最后更新：{res['update_time']}
                -------------------------\n
                """)
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"查询流量失败：{e}\n")
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="查看园区流量", command=view_all_flow, width=15).grid(row=7, column=0, columnspan=2, pady=5)

    # ========== 功能4：设备管理 - 查看故障设备 ==========
    def view_error_device():
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
            WHERE d.run_status IN ('故障', '离线')
            ORDER BY d.run_status
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            scroll_text.insert(tk.INSERT, f"【故障/离线设备】共{len(results)}台\n")
            scroll_text.insert(tk.INSERT, "="*80 + "\n")
            for res in results:
                scroll_text.insert(tk.INSERT, f"""
                设备编号：{res['device_id']} | 类型：{res['device_type']}
                部署区域：{res['area_name']} | 状态：{res['run_status']}
                安装时间：{res['install_time']} | 最后校准：{res['last_calibrate_time'] or '未校准'}
                -------------------------\n
                """)
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"查询设备失败：{e}\n")
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="查看故障设备", command=view_error_device, width=15).grid(row=8, column=0, columnspan=2, pady=5)

    # ========== 退出按钮 ==========
    tk.Button(left_frame, text="退出", command=window.destroy, width=15, bg="#ff4444", fg="white").grid(row=9, column=0, columnspan=2, pady=20)

    window.mainloop()