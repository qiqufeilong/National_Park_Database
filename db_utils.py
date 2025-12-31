import pymysql
from hashlib import sha256, md5


DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'sunhao13ad,',
    'database': 'np_management',
    'charset': 'utf8mb4'
}

def get_db_conn():
    """获取数据库连接"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"数据库连接失败：{e}")
        return None

def encrypt_pwd(pwd):
    """密码加密（SHA-256）"""
    """MD5加密密码（匹配数据库中的密码）"""
    return md5(pwd.encode()).hexdigest()