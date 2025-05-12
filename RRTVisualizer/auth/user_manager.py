"""
用户管理模块
提供用户注册、验证和管理功能
"""

import os
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Optional, List, Any
from werkzeug.security import generate_password_hash, check_password_hash


class User:
    """用户类，表示单个用户的数据结构"""

    def __init__(self, username: str, email: str, password_hash: str, user_id: str = None,
                 created_at: str = None, last_login: str = None, is_active: bool = True):
        """
        初始化用户对象

        参数:
            username: 用户名
            email: 电子邮件
            password_hash: 密码哈希
            user_id: 用户ID（如果为None则自动生成）
            created_at: 创建时间（如果为None则使用当前时间）
            last_login: 最后登录时间
            is_active: 账户是否激活
        """
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.user_id = user_id if user_id else str(uuid.uuid4())
        self.created_at = created_at if created_at else datetime.now().isoformat()
        self.last_login = last_login
        self.is_active = is_active

    def to_dict(self) -> Dict[str, Any]:
        """
        将用户对象转换为字典，用于JSON序列化

        返回:
            用户数据字典
        """
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'is_active': self.is_active
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """
        从字典创建用户对象

        参数:
            data: 用户数据字典

        返回:
            User: 用户对象
        """
        return cls(
            username=data['username'],
            email=data['email'],
            password_hash=data['password_hash'],
            user_id=data['user_id'],
            created_at=data['created_at'],
            last_login=data['last_login'],
            is_active=data.get('is_active', True)  # 默认为激活状态
        )

    def check_password(self, password: str) -> bool:
        """
        验证密码

        参数:
            password: 明文密码

        返回:
            bool: 密码是否匹配
        """
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = datetime.now().isoformat()


class UserManager:
    """用户管理类，处理用户数据存储和验证"""

    def __init__(self, data_dir: str = 'users'):
        """
        初始化用户管理器

        参数:
            data_dir: 用户数据存储目录
        """
        # 确定用户数据目录的绝对路径
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(base_dir, data_dir)
        self.users_file = os.path.join(self.data_dir, 'users.json')

        # 确保目录存在
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # 初始化用户字典
        self.users: Dict[str, User] = {}
        self.load_users()

    def load_users(self):
        """从JSON文件加载用户数据"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    users_dict = json.load(f)
                    for username, user_data in users_dict.items():
                        self.users[username] = User.from_dict(user_data)
                print(f"已加载 {len(self.users)} 个用户")
            except Exception as e:
                print(f"加载用户数据时出错: {e}")
                self.users = {}
        else:
            print("用户数据文件不存在，创建新的空数据")
            self.save_users()  # 创建空的用户数据文件

    def save_users(self):
        """将用户数据保存到JSON文件"""
        try:
            # 转换用户对象为可JSON序列化的字典
            users_dict = {username: user.to_dict() for username, user in self.users.items()}

            # 确保目录存在
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)

            # 先写入临时文件，然后重命名，防止写入过程中的中断导致数据损坏
            temp_file = f"{self.users_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(users_dict, f, indent=2, ensure_ascii=False)

            # 在Windows上，如果目标文件存在，os.rename可能会失败
            # 所以先检查并删除目标文件
            if os.path.exists(self.users_file):
                os.remove(self.users_file)

            os.rename(temp_file, self.users_file)
            return True
        except Exception as e:
            print(f"保存用户数据时出错: {e}")
            return False

    def create_user(self, username: str, email: str, password: str) -> Optional[User]:
        """
        创建新用户

        参数:
            username: 用户名
            email: 电子邮件
            password: 明文密码

        返回:
            User: 创建的用户对象，如果创建失败则返回None
        """
        # 检查用户名是否已存在
        if username in self.users:
            print(f"用户名 '{username}' 已存在")
            return None

        # 检查邮箱是否已被使用
        for user in self.users.values():
            if user.email == email:
                print(f"邮箱 '{email}' 已被使用")
                return None

        # 创建用户目录
        user_dir = os.path.join(self.data_dir, username)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)

        # 哈希密码
        password_hash = generate_password_hash(password)

        # 创建用户对象
        user = User(username, email, password_hash)
        self.users[username] = user

        # 保存用户数据
        if self.save_users():
            return user
        return None

    def get_user(self, username: str) -> Optional[User]:
        """
        按用户名获取用户

        参数:
            username: 用户名

        返回:
            User: 用户对象，如果不存在则返回None
        """
        return self.users.get(username)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        按电子邮件获取用户

        参数:
            email: 电子邮件

        返回:
            User: 用户对象，如果不存在则返回None
        """
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        验证用户凭据

        参数:
            username: 用户名
            password: 明文密码

        返回:
            User: 验证成功的用户对象，如果验证失败则返回None
        """
        user = self.get_user(username)
        if user and user.is_active and user.check_password(password):
            # 更新最后登录时间
            user.update_last_login()
            self.save_users()
            return user
        return None

    def update_user(self, username: str, **kwargs) -> bool:
        """
        更新用户信息

        参数:
            username: 要更新的用户
            **kwargs: 要更新的字段及其值

        返回:
            bool: 更新是否成功
        """
        user = self.get_user(username)
        if not user:
            return False

        # 更新用户字段
        for key, value in kwargs.items():
            if hasattr(user, key) and key != 'username' and key != 'user_id':
                # 如果是密码字段，需要哈希处理
                if key == 'password':
                    user.password_hash = generate_password_hash(value)
                else:
                    setattr(user, key, value)

        return self.save_users()

    def delete_user(self, username: str) -> bool:
        """
        删除用户

        参数:
            username: 要删除的用户名

        返回:
            bool: 删除是否成功
        """
        if username in self.users:
            del self.users[username]
            return self.save_users()
        return False

    def save_user_config(self, username: str, config_name: str, config_data: Dict) -> bool:
        """
        保存用户配置

        参数:
            username: 用户名
            config_name: 配置名称
            config_data: 配置数据

        返回:
            bool: 保存是否成功
        """
        if username not in self.users:
            return False

        user_dir = os.path.join(self.data_dir, username)
        configs_file = os.path.join(user_dir, 'configs.json')

        # 加载现有配置或创建新的
        configs = {}
        if os.path.exists(configs_file):
            try:
                with open(configs_file, 'r', encoding='utf-8') as f:
                    configs = json.load(f)
            except:
                configs = {}

        # 添加或更新配置
        configs[config_name] = {
            'data': config_data,
            'created_at': datetime.now().isoformat()
        }

        # 保存配置
        try:
            with open(configs_file, 'w', encoding='utf-8') as f:
                json.dump(configs, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存用户配置时出错: {e}")
            return False

    def get_user_configs(self, username: str) -> Dict:
        """
        获取用户所有配置

        参数:
            username: 用户名

        返回:
            Dict: 用户配置字典
        """
        if username not in self.users:
            return {}

        user_dir = os.path.join(self.data_dir, username)
        configs_file = os.path.join(user_dir, 'configs.json')

        if not os.path.exists(configs_file):
            return {}

        try:
            with open(configs_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"获取用户配置时出错: {e}")
            return {}

    def get_user_config(self, username: str, config_name: str) -> Optional[Dict]:
        """
        获取用户特定配置

        参数:
            username: 用户名
            config_name: 配置名称

        返回:
            Dict: 配置数据，如果不存在则返回None
        """
        configs = self.get_user_configs(username)
        return configs.get(config_name)

    def delete_user_config(self, username: str, config_name: str) -> bool:
        """
        删除用户配置

        参数:
            username: 用户名
            config_name: 配置名称

        返回:
            bool: 删除是否成功
        """
        if username not in self.users:
            return False

        configs = self.get_user_configs(username)
        if config_name not in configs:
            return False

        # 删除配置
        del configs[config_name]

        # 保存更新后的配置
        user_dir = os.path.join(self.data_dir, username)
        configs_file = os.path.join(user_dir, 'configs.json')

        try:
            with open(configs_file, 'w', encoding='utf-8') as f:
                json.dump(configs, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"删除用户配置时出错: {e}")
            return False