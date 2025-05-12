"""
RRTVisualizer - 认证模块
实现简单的基于文件的用户认证系统
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from flask import session, redirect, url_for, flash, request

# 用户数据文件路径
USER_DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'users.json')

# 确保data目录存在
os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)


def hash_password(password, salt=None):
    """
    使用SHA-256哈希算法和盐值对密码进行哈希处理

    参数:
        password: 明文密码
        salt: 盐值，如果不提供则生成新的

    返回:
        (hashed_password, salt): 哈希后的密码和盐值
    """
    if salt is None:
        salt = secrets.token_hex(16)

    # 组合密码和盐值，然后哈希
    pw_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return pw_hash, salt


def load_users():
    """
    从文件中加载用户数据

    返回:
        users: 用户字典 {username: user_data}
    """
    if not os.path.exists(USER_DATA_FILE):
        return {}

    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_users(users):
    """
    将用户数据保存到文件

    参数:
        users: 用户字典 {username: user_data}
    """
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f, indent=4)


def register_user(username, password, email):
    """
    注册新用户

    参数:
        username: 用户名
        password: 密码
        email: 电子邮箱

    返回:
        success: 是否成功注册
        message: 结果消息
    """
    users = load_users()

    # 检查用户名是否已存在
    if username in users:
        return False, "用户名已被使用"

    # 检查邮箱是否已被使用
    for user in users.values():
        if user.get('email') == email:
            return False, "邮箱已被注册"

    # 哈希密码
    pw_hash, salt = hash_password(password)

    # 创建用户记录
    users[username] = {
        'username': username,
        'password_hash': pw_hash,
        'salt': salt,
        'email': email,
        'created_at': datetime.now().isoformat(),
        'last_login': None,
        'preferences': {}
    }

    # 保存用户数据
    save_users(users)

    return True, "注册成功！"


def verify_user(username, password):
    """
    验证用户登录

    参数:
        username: 用户名
        password: 密码

    返回:
        success: 是否登录成功
        user: 用户数据（如果成功）或错误消息（如果失败）
    """
    users = load_users()

    # 检查用户名是否存在
    if username not in users:
        return False, "用户名或密码不正确"

    user = users[username]

    # 验证密码
    pw_hash, _ = hash_password(password, user['salt'])
    if pw_hash != user['password_hash']:
        return False, "用户名或密码不正确"

    # 更新最后登录时间
    user['last_login'] = datetime.now().isoformat()
    save_users(users)

    return True, user


def is_logged_in():
    """
    检查用户是否已登录

    返回:
        bool: 是否已登录
    """
    return 'user_id' in session


def get_current_user():
    """
    获取当前登录用户的信息

    返回:
        user: 用户数据或None（如果未登录）
    """
    if not is_logged_in():
        return None

    users = load_users()
    return users.get(session['user_id'])


def login_required(view_func):
    """
    用于视图函数的登录验证装饰器
    """

    def wrapper(*args, **kwargs):
        if not is_logged_in():
            # 保存用户正要访问的URL，以便登录后重定向
            session['next_url'] = request.url
            flash('请先登录再访问此页面', 'warning')
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)

    # 确保Flask能正确识别装饰后的函数名称
    wrapper.__name__ = view_func.__name__
    return wrapper


def update_user_preferences(username, preferences):
    """
    更新用户偏好设置

    参数:
        username: 用户名
        preferences: 偏好设置字典

    返回:
        success: 是否成功更新
    """
    users = load_users()

    if username not in users:
        return False

    # 更新偏好设置
    users[username]['preferences'] = preferences
    save_users(users)

    return True