import schedule
import time
import db_utils
import random
import datetime
import pymysql

def simulate_env_monitor():
    """模拟环境监测数据更新（每1分钟）"""
    conn = db_utils.get_db_conn()
    if not conn:
        print("数据库连接失败，环境模拟停止")
        return

    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # 获取正常运行的环境监测设备
        cursor.execute("""
        SELECT device_id, deploy_area_id FROM np_monitor_device
        WHERE device_type IN ('水质监测仪', '空气质量传感器', '土壤湿度传感器') AND run_status='正常'
        """)
        devices = cursor.fetchall()

        # 获取所有监测指标
        cursor.execute("SELECT index_id, threshold_upper, threshold_lower FROM np_env_index")
        indexes = cursor.fetchall()
        if not indexes:
            print("无监测指标，环境模拟停止")
            return

        for device in devices:
            device_id = device['device_id']
            area_id = device['deploy_area_id']
            # 随机选一个指标
            index = random.choice(indexes)
            index_id = index['index_id']
            upper = index['threshold_upper']
            lower = index['threshold_lower']

            # 生成模拟值（90%概率在阈值内，10%异常）
            base_value = (upper + lower) / 2
            if random.random() < 0.1:
                # 异常值
                monitor_value = round(base_value + random.uniform(1, 2) * (upper - base_value), 2)
                is_abnormal = 1
                data_quality = "差"
            else:
                # 正常值
                monitor_value = round(base_value + random.uniform(-0.5, 0.5), 2)
                is_abnormal = 0
                data_quality = "优" if abs(monitor_value - base_value) < 0.2 else "良"

            # 插入监测数据
            env_data_id = f"ED{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            cursor.execute("""
            INSERT INTO np_env_monitor 
            (env_data_id, index_id, device_id, collect_time, monitor_value, area_id, data_quality, is_abnormal)
            VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s)
            """, (env_data_id, index_id, device_id, monitor_value, area_id, data_quality, is_abnormal))

        conn.commit()
        print(f"[{datetime.datetime.now()}] 环境模拟完成，更新{len(devices)}台设备数据")
    except Exception as e:
        print(f"环境模拟失败：{e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# 启动定时任务
if __name__ == "__main__":
    print("环境监测模拟启动...")
    schedule.every(1).minutes.do(simulate_env_monitor)
    while True:
        schedule.run_pending()
        time.sleep(1)