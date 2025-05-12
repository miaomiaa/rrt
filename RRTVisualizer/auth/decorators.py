"""
认证装饰器模块
提供访问控制功能
"""

from functools import wraps
from flask import session, redirect, url_for, request, flash


def login_required(f):
    """
    要求用户登录的装饰器
    如果用户未登录，则重定向到登录页面

    使用方式:
    @login_required
    def protected_route():
        # 只有登录用户可以访问
        pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # 保存当前URL，以便登录后重定向回来
            next_url = request.url
            flash('请先登录以访问该页面', 'warning')
            return redirect(url_for('login', next=next_url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    要求管理员权限的装饰器
    如果用户不是管理员，则重定向到首页

    使用方式:
    @admin_required
    def admin_route():
        # 只有管理员可以访问
        pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin', False):
            flash('您没有权限访问该页面', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function