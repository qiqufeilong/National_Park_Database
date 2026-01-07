import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import db_utils
import pymysql
import datetime

def open(user_id, real_name):
    # 新增：登录参数空值校验，避免传递空值导致加载异常
    if not user_id or not real_name:
        messagebox.showerror("登录错误", "用户信息为空！请重新登录")
        return
    
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
    
    # 新增：登录成功提示，确认页面加载正常
    scroll_text.insert(tk.INSERT, f"✅ 公园管理人员 {real_name}（ID：{user_id}）登录成功！\n")
    scroll_text.insert(tk.INSERT, f"登录时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    scroll_text.insert(tk.INSERT, "="*100 + "\n")

    # ========== 功能1：查看全系统业务汇总（增强错误捕获） ==========
    def view_business_summary():
        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "❌ 数据库连接失败！\n")
            messagebox.showerror("数据库错误", "无法连接数据库，请联系管理员")
            return

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            scroll_text.insert(tk.INSERT, f"\n【全系统业务汇总】{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            scroll_text.insert(tk.INSERT, "="*100 + "\n")

            # 1. 流量汇总
            cursor.execute("""
            SELECT a.area_name, f.real_time_people, f.max_capacity, f.current_status 
            FROM np_flow_control f
            JOIN np_area a ON f.area_id = a.area_id
            """)
            flow_res = cursor.fetchall()
            scroll_text.insert(tk.INSERT, "■ 区域流量状态：\n")
            if flow_res:
                for res in flow_res:
                    area_name = res.get('area_name', '未知区域')
                    real_time_people = res.get('real_time_people', 0)
                    max_capacity = res.get('max_capacity', 0)
                    current_status = res.get('current_status', '未知状态')
                    scroll_text.insert(tk.INSERT, f"  {area_name}：{real_time_people}/{max_capacity} 人 | 状态：{current_status}\n")
            else:
                scroll_text.insert(tk.INSERT, "  暂无流量数据\n")

            # 2. 非法行为汇总
            cursor.execute("""
            SELECT handle_status, COUNT(*) AS count 
            FROM np_illegal_behavior 
            GROUP BY handle_status
            """)
            illegal_res = cursor.fetchall()
            scroll_text.insert(tk.INSERT, "\n■ 非法行为处理状态：\n")
            if illegal_res:
                for res in illegal_res:
                    handle_status = res.get('handle_status', '未知状态')
                    count = res.get('count', 0)
                    scroll_text.insert(tk.INSERT, f"  {handle_status}：{count} 条\n")
            else:
                scroll_text.insert(tk.INSERT, "  暂无非法行为数据\n")

            # 3. 科研项目汇总
            cursor.execute("""
            SELECT project_status, COUNT(*) AS count 
            FROM np_research_project 
            GROUP BY project_status
            """)
            proj_res = cursor.fetchall()
            scroll_text.insert(tk.INSERT, "\n■ 科研项目状态：\n")
            if proj_res:
                for res in proj_res:
                    project_status = res.get('project_status', '未知状态')
                    count = res.get('count', 0)
                    scroll_text.insert(tk.INSERT, f"  {project_status}：{count} 个\n")
            else:
                scroll_text.insert(tk.INSERT, "  暂无科研项目数据\n")

            # 4. 环境异常汇总
            cursor.execute("SELECT COUNT(*) AS count FROM np_env_monitor WHERE is_abnormal=1 AND collect_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)")
            env_res = cursor.fetchone()
            env_count = env_res.get('count', 0) if env_res else 0
            scroll_text.insert(tk.INSERT, f"\n■ 近24小时环境异常数据：{env_count} 条\n")

            scroll_text.insert(tk.INSERT, "="*100 + "\n")
        except pymysql.Error as e:
            err_msg = f"SQL执行失败【错误码{e.args[0]}】：{e.args[1]}"
            scroll_text.insert(tk.INSERT, f"❌ 查询汇总失败：{err_msg}\n")
            messagebox.showerror("SQL错误", err_msg)
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"❌ 查询汇总失败：{str(e)}\n")
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="查看业务汇总", command=view_business_summary, width=20).grid(row=0, column=0, pady=10)

    # ========== 功能2：审批科研项目（核心修复：Entry的value参数） ==========
    tk.Label(left_frame, text="审批科研项目", font=("黑体", 12)).grid(row=1, column=0, columnspan=2, pady=10)
    tk.Label(left_frame, text="项目编号：").grid(row=2, column=0, sticky="w")
    entry_proj_id = tk.Entry(left_frame, width=20)
    entry_proj_id.grid(row=2, column=1)
    
    tk.Label(left_frame, text="审批结果：").grid(row=3, column=0, sticky="w")
    entry_approve = tk.Entry(left_frame, width=20)
    # 修复：删除value参数，用insert设置默认值（tkinter标准写法）
    entry_approve.insert(0, "通过")
    entry_approve.grid(row=3, column=1)

    def approve_project():
        project_id = entry_proj_id.get().strip()
        approve_result = entry_approve.get().strip()
        
        # 强化空值校验
        if not project_id:
            messagebox.showwarning("输入错误", "项目编号不能为空！")
            return
        if not approve_result:
            messagebox.showwarning("输入错误", "审批结果不能为空！")
            return

        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "❌ 数据库连接失败！\n")
            messagebox.showerror("数据库错误", "无法连接数据库，请联系管理员")
            return

        cursor = conn.cursor()
        try:
            # 先校验项目是否存在
            cursor.execute("SELECT 1 FROM np_research_project WHERE project_id=%s", (project_id,))
            if not cursor.fetchone():
                scroll_text.insert(tk.INSERT, f"❌ 审批失败！未找到项目{project_id}\n")
                messagebox.showinfo("审批结果", f"未查询到项目{project_id}，请核对编号")
                return
            
            # 更新项目状态（通过/驳回）
            status = "在研" if approve_result == "通过" else "暂停"
            sql = """
            UPDATE np_research_project 
            SET project_status=%s, update_time=NOW()
            WHERE project_id=%s
            """
            cursor.execute(sql, (status, project_id))
            conn.commit()
            scroll_text.insert(tk.INSERT, f"✅ 项目{project_id}审批完成！结果：{approve_result}，状态：{status}\n")
        except pymysql.Error as e:
            err_msg = f"SQL执行失败【错误码{e.args[0]}】：{e.args[1]}"
            scroll_text.insert(tk.INSERT, f"❌ 审批失败：{err_msg}\n")
            messagebox.showerror("SQL错误", err_msg)
            conn.rollback()
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"❌ 审批失败：{str(e)}\n")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="提交审批", command=approve_project, width=20).grid(row=4, column=0, columnspan=2, pady=5)

    # ========== 功能3：配置流量控制策略（增强校验） ==========
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
        
        # 强化空值+格式校验
        if not area_id:
            messagebox.showwarning("输入错误", "区域编号不能为空！")
            return
        if not threshold:
            messagebox.showwarning("输入错误", "预警阈值不能为空！")
            return
        
        try:
            threshold = int(threshold)
            if threshold < 0 or threshold > 10000:  # 增加合理范围校验
                raise ValueError
        except ValueError:
            messagebox.showwarning("格式错误", "预警阈值必须为0-10000之间的整数！")
            return

        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "❌ 数据库连接失败！\n")
            messagebox.showerror("数据库错误", "无法连接数据库，请联系管理员")
            return

        cursor = conn.cursor()
        try:
            # 先校验区域ID是否存在
            cursor.execute("SELECT 1 FROM np_area WHERE area_id=%s", (area_id,))
            if not cursor.fetchone():
                # 查询合法区域ID提示用户
                cursor.execute("SELECT area_id, area_name FROM np_area")
                valid_areas = cursor.fetchall()
                area_tips = "合法区域ID：\n" + "\n".join([f"{id} - {name}" for id, name in valid_areas])
                scroll_text.insert(tk.INSERT, f"❌ 区域ID {area_id} 不存在！\n")
                messagebox.showwarning("区域错误", f"区域ID {area_id} 不存在！\n{area_tips}")
                return
            
            # 更新流量预警阈值
            sql = """
            UPDATE np_flow_control 
            SET warn_threshold=%s, update_time=NOW()
            WHERE area_id=%s
            """
            cursor.execute(sql, (threshold, area_id))
            if cursor.rowcount > 0:
                conn.commit()
                scroll_text.insert(tk.INSERT, f"✅ 区域{area_id}流量策略配置成功！预警阈值：{threshold}\n")
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
                scroll_text.insert(tk.INSERT, f"✅ 区域{area_id}流量策略创建成功！预警阈值：{threshold}\n")
        except pymysql.Error as e:
            err_msg = f"SQL执行失败【错误码{e.args[0]}】：{e.args[1]}"
            scroll_text.insert(tk.INSERT, f"❌ 配置失败：{err_msg}\n")
            messagebox.showerror("SQL错误", err_msg)
            conn.rollback()
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"❌ 配置失败：{str(e)}\n")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="配置阈值", command=config_flow, width=20).grid(row=8, column=0, columnspan=2, pady=5)

    # ========== 功能4：查看预警信息（增强空值处理） ==========
    def view_warning():
        conn = db_utils.get_db_conn()
        if not conn:
            scroll_text.insert(tk.INSERT, "❌ 数据库连接失败！\n")
            messagebox.showerror("数据库错误", "无法连接数据库，请联系管理员")
            return

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            scroll_text.insert(tk.INSERT, f"\n【系统预警信息】{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            scroll_text.insert(tk.INSERT, "="*80 + "\n")

            # 1. 流量预警
            cursor.execute("""
            SELECT a.area_name, f.real_time_people, f.warn_threshold 
            FROM np_flow_control f
            JOIN np_area a ON f.area_id = a.area_id
            WHERE f.current_status='预警'
            """)
            flow_warn = cursor.fetchall()
            scroll_text.insert(tk.INSERT, "■ 流量预警：\n")
            if flow_warn:
                for res in flow_warn:
                    area_name = res.get('area_name', '未知区域')
                    real_time_people = res.get('real_time_people', 0)
                    warn_threshold = res.get('warn_threshold', 0)
                    scroll_text.insert(tk.INSERT, f"  {area_name}：{real_time_people} 人（阈值{warn_threshold}）\n")
            else:
                scroll_text.insert(tk.INSERT, "  无\n")

            # 2. 环境异常预警
            cursor.execute("""
            SELECT a.area_name, i.index_name, e.monitor_value, e.collect_time 
            FROM np_env_monitor e
            JOIN np_area a ON e.area_id = a.area_id
            JOIN np_env_index i ON e.index_id = i.index_id
            WHERE e.is_abnormal=1 AND e.collect_time >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
            """)
            env_warn = cursor.fetchall()
            scroll_text.insert(tk.INSERT, "\n■ 环境异常预警（近1小时）：\n")
            if env_warn:
                for res in env_warn:
                    area_name = res.get('area_name', '未知区域')
                    index_name = res.get('index_name', '未知指标')
                    monitor_value = res.get('monitor_value', '无数据')
                    collect_time = res.get('collect_time', '未知时间')
                    scroll_text.insert(tk.INSERT, f"  {area_name} | {index_name}：{monitor_value} | 时间：{collect_time}\n")
            else:
                scroll_text.insert(tk.INSERT, "  无\n")

            # 3. 非法行为预警
            cursor.execute("""
            SELECT a.area_name, i.behavior_type, i.occur_time 
            FROM np_illegal_behavior i
            JOIN np_area a ON i.area_id = a.area_id
            WHERE i.handle_status='未处理'
            """)
            illegal_warn = cursor.fetchall()
            scroll_text.insert(tk.INSERT, "\n■ 未处理非法行为预警：\n")
            if illegal_warn:
                for res in illegal_warn:
                    area_name = res.get('area_name', '未知区域')
                    behavior_type = res.get('behavior_type', '未知类型')
                    occur_time = res.get('occur_time', '未知时间')
                    scroll_text.insert(tk.INSERT, f"  {area_name} | {behavior_type} | 时间：{occur_time}\n")
            else:
                scroll_text.insert(tk.INSERT, "  无\n")

            scroll_text.insert(tk.INSERT, "="*80 + "\n")
        except pymysql.Error as e:
            err_msg = f"SQL执行失败【错误码{e.args[0]}】：{e.args[1]}"
            scroll_text.insert(tk.INSERT, f"❌ 查询预警失败：{err_msg}\n")
            messagebox.showerror("SQL错误", err_msg)
        except Exception as e:
            scroll_text.insert(tk.INSERT, f"❌ 查询预警失败：{str(e)}\n")
        finally:
            cursor.close()
            conn.close()

    tk.Button(left_frame, text="查看预警信息", command=view_warning, width=20).grid(row=9, column=0, columnspan=2, pady=5)

    # ========== 退出按钮（新增确认弹窗） ==========
    def safe_quit():
        if messagebox.askyesno("退出确认", "确定要退出公园管理人员页面吗？"):
            window.destroy()

    tk.Button(left_frame, text="退出", command=safe_quit, width=20, bg="#ff4444", fg="white").grid(row=10, column=0, columnspan=2, pady=20)

    window.mainloop()

# 测试调用（模拟登录传递参数）
if __name__ == "__main__":
    open("U010", "周九")