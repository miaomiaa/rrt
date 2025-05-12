"""
认证模块
包含用户管理和访问控制功能
"""

from .user_manager import UserManager, User
from .decorators import login_required

# 导出所有相关功能
__all__ = [
    'UserManager',
    'User',
    'login_required'
]