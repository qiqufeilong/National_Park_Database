import tkinter as tk
from tkinter import messagebox
import pymysql
import db_utils

# 导入所有8类角色的页面
from role_pages import (
    monitor_page, analyst_page, tourist_page, law_page, 
    researcher_page, admin_page, manager_page, technician_page
)

def main():
    window = tk.Tk()
    window.title("国家公园智慧管理系统")
    window.geometry("500x300")

    # 界面组件
    tk.Label(window, text="账号").grid(row=0, column=0, padx=20, pady=30)
    tk.Label(window, text="密码").grid(row=1, column=0, padx=20, pady=10)
    entry_account = tk.Entry(window, width=30)
    entry_pwd = tk.Entry(window, width=30, show="*")
    entry_account.grid(row=0, column=1)
    entry_pwd.grid(row=1, column=1)

    def login():
        # 1. 获取并校验输入
        account = entry_account.get().strip()
        pwd = entry_pwd.get().strip()
        if not account or not pwd:
            messagebox.showwarning("警告", "账号或密码不能为空！")
            return

        # 2. 提前定义user变量（避免未定义报错）
        user = None
        conn = None
        cursor = None

        try:
            # 3. 连接数据库
            conn = db_utils.get_db_conn()
            if not conn:
                messagebox.showerror("错误", "数据库连接失败！")
                return

            # 4. 调试打印：加密后的密码+SQL参数
            encrypt_pwd_val = db_utils.encrypt_pwd(pwd)
            print(f"输入账号：{account}")
            print(f"加密后密码：{encrypt_pwd_val}")

            # 5. 查询用户
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            sql = "SELECT user_id, role_type, real_name FROM np_user WHERE user_account=%s AND user_pwd=%s"
            print(f"执行SQL：{sql}，参数：({account}, {encrypt_pwd_val})")
            
            cursor.execute(sql, (account, encrypt_pwd_val))
            user = cursor.fetchone()
            print(f"数据库查询结果：{user}")  # 此时user已定义，不会报错

            # 6. 验证登录结果
            if user:
                messagebox.showinfo("成功", f"欢迎{user['real_name']}登录！")
                window.destroy()
                # 按角色跳转对应页面
                role = user['role_type']
                if role == 'monitor':
                    monitor_page.open(user['user_id'], user['real_name'])
                elif role == 'analyst':
                    analyst_page.open(user['user_id'], user['real_name'])
                elif role == 'tourist':
                    tourist_page.open(user['user_id'], user['real_name'])
                elif role == 'law':
                    law_page.open(user['user_id'], user['real_name'])
                elif role == 'researcher':
                    researcher_page.open(user['user_id'], user['real_name'])
                elif role == 'admin':
                    admin_page.open(user['user_id'], user['real_name'])
                elif role == 'manager':
                    manager_page.open(user['user_id'], user['real_name'])
                elif role == 'technician':
                    technician_page.open(user['user_id'], user['real_name'])
                else:
                    messagebox.showerror("错误", "未知角色类型！")
            else:
                messagebox.showerror("错误", "账号或密码错误！")

        except Exception as e:
            messagebox.showerror("错误", f"登录失败：{str(e)}")
        finally:
            # 确保游标和连接关闭（避免资源泄露）
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # 登录按钮
    tk.Button(window, text="登录", command=login, width=20, height=1).grid(row=2, column=1, pady=20)
    window.mainloop()

if __name__ == "__main__":
    main()