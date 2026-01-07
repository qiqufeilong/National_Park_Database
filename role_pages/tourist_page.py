import tkinter as tk
from tkinter import scrolledtext, messagebox
import db_utils
import pymysql
import datetime

# 将所有功能封装在一个类中
class TouristPage:
    def __init__(self, master, user_id, real_name):
        self.master = master
        self.master.title(f"游客-{real_name}")
        self.master.geometry("800x600")
        
        self.user_id = user_id
        self.real_name = real_name

        # 布局
        self.create_widgets()

    def create_widgets(self):
        left_frame = tk.Frame(self.master)
        left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="n")
        right_frame = tk.Frame(self.master)
        right_frame.grid(row=0, column=1, padx=20, pady=20)

        # 结果区
        self.scroll_text = scrolledtext.ScrolledText(right_frame, width=60, height=30)
        self.scroll_text.pack()

        # ========== 功能1：预约入园 ==========
        tk.Label(left_frame, text="预约入园", font=("黑体", 12)).grid(row=0, column=0, columnspan=2, pady=10)
        
        # 使用 self. 将输入框定义为类的属性
        tk.Label(left_frame, text="预约区域：").grid(row=1, column=0, sticky="w")
        self.entry_area = tk.Entry(left_frame, width=20)
        self.entry_area.grid(row=1, column=1)

        tk.Label(left_frame, text="预约日期：").grid(row=2, column=0, sticky="w")
        self.entry_date = tk.Entry(left_frame, width=20)
        self.entry_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.entry_date.grid(row=2, column=1)

        tk.Label(left_frame, text="入园时段：").grid(row=3, column=0, sticky="w")
        self.entry_period = tk.Entry(left_frame, width=20)
        self.entry_period.insert(0, "09:00-12:00")
        self.entry_period.grid(row=3, column=1)

        tk.Label(left_frame, text="同行人数：").grid(row=4, column=0, sticky="w")
        self.entry_peer = tk.Entry(left_frame, width=20)
        self.entry_peer.insert(0, "1")   
        self.entry_peer.grid(row=4, column=1)

        tk.Button(left_frame, text="提交预约", command=self.reserve_enter, width=15).grid(row=5, column=0, columnspan=2, pady=5)

        # ========== 功能2：确认入园 ==========
        tk.Button(left_frame, text="确认入园", command=self.confirm_enter, width=15).grid(row=6, column=0, columnspan=2, pady=5)

        # ========== 功能3：查看我的预约 ==========
        tk.Button(left_frame, text="查看我的预约", command=self.view_my_reserve, width=15).grid(row=7, column=0, columnspan=2, pady=5)

        # ========== 功能4：查看实时位置 ==========
        tk.Button(left_frame, text="查看实时位置", command=self.view_my_track, width=15).grid(row=8, column=0, columnspan=2, pady=5)

        # ========== 退出按钮 ==========
        tk.Button(left_frame, text="退出", command=self.master.destroy, width=15, bg="#ff4444", fg="white").grid(row=9, column=0, columnspan=2, pady=20)

    def reserve_enter(self):
        # 通过 self. 访问类的属性
        area_id = self.entry_area.get().strip()
        reserve_date = self.entry_date.get().strip()
        entry_period = self.entry_period.get().strip()
        peer_num_str = self.entry_peer.get().strip()

        if not all([area_id, reserve_date, entry_period, peer_num_str]):
            messagebox.showwarning("警告", "请填写完整预约信息！")
            return

        try:
            peer_num = int(peer_num_str)
            if peer_num < 1:
                raise ValueError
        except ValueError:
            messagebox.showwarning("警告", "同行人数必须为正整数！")
            return

        conn = db_utils.get_db_conn()
        if not conn:
            self.scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor()
        reserve_id = f"TR{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        ticket_amount = peer_num * 120
        try:
            sql1 = """
            INSERT INTO np_tourist_reserve 
            (reserve_id, tourist_id, reserve_date, entry_period, peer_num, reserve_status, ticket_amount, pay_status, area_id)
            VALUES (%s, %s, %s, %s, %s, '已确认', %s, '已支付', %s)
            """
            cursor.execute(sql1, (reserve_id, self.user_id, reserve_date, entry_period, peer_num, ticket_amount, area_id))

            sql2 = "UPDATE np_tourist_info SET reserve_id=%s WHERE tourist_id=%s"
            cursor.execute(sql2, (reserve_id, self.user_id))

            conn.commit()
            self.scroll_text.insert(tk.INSERT, f"预约成功！预约编号：{reserve_id}\n")
            self.scroll_text.insert(tk.INSERT, f"预约区域：{area_id} | 日期：{reserve_date} | 人数：{peer_num}\n")
            self.scroll_text.insert(tk.INSERT, f"总费用：{ticket_amount}元 | 状态：已确认\n")
        except Exception as e:
            self.scroll_text.insert(tk.INSERT, f"预约失败：{e}\n")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def confirm_enter(self):
        # ... (此函数逻辑不变，只需将 scroll_text 改为 self.scroll_text)
        conn = db_utils.get_db_conn()
        if not conn:
            self.scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            sql1 = """
            SELECT reserve_id, area_id, peer_num FROM np_tourist_reserve
            WHERE tourist_id=%s AND reserve_status='已确认' AND reserve_date=%s
            """
            cursor.execute(sql1, (self.user_id, datetime.date.today().strftime("%Y-%m-%d")))
            reserve = cursor.fetchone()
            if not reserve:
                self.scroll_text.insert(tk.INSERT, "暂无今日有效预约！\n")
                return

            sql2 = "UPDATE np_tourist_info SET entry_time=NOW() WHERE tourist_id=%s"
            cursor.execute(sql2, (self.user_id,))

            sql3 = "UPDATE np_flow_control SET real_time_people = real_time_people + %s WHERE area_id=%s"
            cursor.execute(sql3, (reserve['peer_num'], reserve['area_id']))

            track_id = f"TT{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            sql4 = """
            INSERT INTO np_tourist_track 
            (track_id, tourist_id, locate_time, track_lng, track_lat, area_id, is_over_route)
            VALUES (%s, %s, NOW(), 103.825000, 30.050000, %s, 0)
            """
            cursor.execute(sql4, (track_id, self.user_id, reserve['area_id']))

            conn.commit()
            self.scroll_text.insert(tk.INSERT, f"入园成功！预约编号：{reserve['reserve_id']}\n")
            self.scroll_text.insert(tk.INSERT, f"所在区域：{reserve['area_id']} | 同行人数：{reserve['peer_num']}\n")
        except Exception as e:
            self.scroll_text.insert(tk.INSERT, f"入园失败：{e}\n")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def view_my_reserve(self):
        # ... (此函数逻辑不变，只需将 scroll_text 改为 self.scroll_text)
        conn = db_utils.get_db_conn()
        if not conn:
            self.scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            sql = """
            SELECT r.*, a.area_name 
            FROM np_tourist_reserve r
            JOIN np_area a ON r.area_id = a.area_id
            WHERE r.tourist_id=%s
            ORDER BY r.reserve_date DESC
            """
            cursor.execute(sql, (self.user_id,))
            results = cursor.fetchall()
            self.scroll_text.insert(tk.INSERT, f"【我的预约记录】共{len(results)}条\n")
            self.scroll_text.insert(tk.INSERT, "="*80 + "\n")
            for res in results:
                self.scroll_text.insert(tk.INSERT, f"""
                预约编号：{res['reserve_id']} | 区域：{res['area_name']}
                日期：{res['reserve_date']} | 时段：{res['entry_period']}
                人数：{res['peer_num']} | 费用：{res['ticket_amount']}元
                状态：{res['reserve_status']} | 支付状态：{res['pay_status']}
                -------------------------\n
                """)
        except Exception as e:
            self.scroll_text.insert(tk.INSERT, f"查询预约失败：{e}\n")
        finally:
            cursor.close()
            conn.close()

    def view_my_track(self):
        # ... (此函数逻辑不变，只需将 scroll_text 改为 self.scroll_text)
        conn = db_utils.get_db_conn()
        if not conn:
            self.scroll_text.insert(tk.INSERT, "数据库连接失败！\n")
            return

        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            sql = """
            SELECT t.*, a.area_name 
            FROM np_tourist_track t
            JOIN np_area a ON t.area_id = a.area_id
            WHERE t.tourist_id=%s ORDER BY t.locate_time DESC LIMIT 1
            """
            cursor.execute(sql, (self.user_id,))
            track = cursor.fetchone()
            if not track:
                self.scroll_text.insert(tk.INSERT, "暂无轨迹数据（未入园）\n")
                return

            self.scroll_text.insert(tk.INSERT, f"【实时位置】{datetime.datetime.now()}\n")
            self.scroll_text.insert(tk.INSERT, f"所在区域：{track['area_name']}\n")
            self.scroll_text.insert(tk.INSERT, f"经纬度：{track['track_lng']}, {track['track_lat']}\n")
            self.scroll_text.insert(tk.INSERT, f"定位时间：{track['locate_time']}\n")
            self.scroll_text.insert(tk.INSERT, f"是否超界：{'是（请立即返回）' if track['is_over_route'] else '否'}\n")
        except Exception as e:
            self.scroll_text.insert(tk.INSERT, f"查询位置失败：{e}\n")
        finally:
            cursor.close()
            conn.close()

# 保留 open 函数以便其他文件调用，但内部逻辑改为创建类的实例
def open(user_id, real_name):
    window = tk.Tk()
    app = TouristPage(window, user_id, real_name)
    window.mainloop()

# 如果你想直接运行这个文件进行测试，可以取消下面的注释
# if __name__ == "__main__":
#     open("U003", "王五")