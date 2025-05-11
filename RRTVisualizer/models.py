# models.py
import sqlite3
import hashlib
from datetime import datetime


class User:
    def __init__(self, db_path='users.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def hash_password(self, password):
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username, email, password):
        """创建新用户"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            password_hash = self.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            ''', (username, email, password_hash))

            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def verify_user(self, username, password):
        """验证用户"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        password_hash = self.hash_password(password)
        cursor.execute('''
            SELECT id, username FROM users
            WHERE (username = ? OR email = ?) AND password_hash = ?
        ''', (username, username, password_hash))

        user = cursor.fetchone()
        conn.close()

        if user:
            return {'id': user[0], 'username': user[1]}
        return None