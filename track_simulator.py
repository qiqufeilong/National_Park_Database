import schedule
import pymysql

import time
import db_utils
import random
import datetime

def simulate_tourist_track():
    """模拟游客轨迹更新（每10秒）"""
    conn = db_utils.get_db_conn()
    if not conn:
        print("数据库连接失败，轨迹模拟停止")
        return

    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # 获取已入园未离园的游客
        cursor.execute("""
        SELECT t.tourist_id, t.area_id FROM np_tourist_info t
        JOIN np_tourist_reserve r ON t.reserve_id = r.reserve_id
        WHERE t.entry_time IS NOT NULL AND t.leave_time IS NULL AND r.reserve_status = '已确认'
        """)
        tourists = cursor.fetchall()

        for tourist in tourists:
            tourist_id = tourist['tourist_id']
            area_id = tourist['area_id']

            # 获取该游客最后一条轨迹
            cursor.execute("""
            SELECT track_lng, track_lat FROM np_tourist_track
            WHERE tourist_id = %s ORDER BY locate_time DESC LIMIT 1
            """, (tourist_id,))
            last_track = cursor.fetchone()

            if last_track:
                # 随机偏移经纬度（模拟移动）
                new_lng = round(float(last_track['track_lng']) + random.uniform(-0.0005, 0.0005), 6)
                new_lat = round(float(last_track['track_lat']) + random.uniform(-0.0005, 0.0005), 6)
            else:
                # 无轨迹时，默认区域中心经纬度
                new_lng = 103.825000
                new_lat = 30.050000

            # 模拟是否超界（随机10%概率）
            is_over_route = 1 if random.random() < 0.1 else 0
            if is_over_route:
                # 超界时生成非法行为记录
                illegal_id = f"IB{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                cursor.execute("""
                INSERT INTO np_illegal_behavior 
                (illegal_id, behavior_type, occur_time, area_id, evidence_path, handle_status)
                VALUES (%s, '游客超界', NOW(), %s, '/upload/illegal/route.jpg', '未处理')
                """, (illegal_id, area_id))

            # 插入新轨迹
            track_id = f"TT{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            cursor.execute("""
            INSERT INTO np_tourist_track 
            (track_id, tourist_id, locate_time, track_lng, track_lat, area_id, is_over_route)
            VALUES (%s, %s, NOW(), %s, %s, %s, %s)
            """, (track_id, tourist_id, new_lng, new_lat, area_id, is_over_route))

        conn.commit()
        print(f"[{datetime.datetime.now()}] 轨迹模拟完成，更新{len(tourists)}名游客轨迹")
    except Exception as e:
        print(f"轨迹模拟失败：{e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# 启动定时任务（每10秒执行）
if __name__ == "__main__":
    print("游客轨迹模拟启动...")
    schedule.every(10).seconds.do(simulate_tourist_track)
    while True:
        schedule.run_pending()
        time.sleep(1)