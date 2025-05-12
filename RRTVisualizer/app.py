#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RRTVisualizer-Web - Web应用主文件
一个基于Web的路径规划算法可视化应用程序，支持用户认证
"""

import os
import json
import numpy as np
import hashlib
import secrets
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, abort, redirect, url_for, session, g, flash, Blueprint

# 导入算法
from algorithms import BaseRRT, RRTStar, RRTConnect, InformedRRT
from environment import ConfigurationSpace, RectangleObstacle, CircleObstacle, PRESETS
from utils.converter import numpy_to_list

# 创建Flask应用
app = Flask(__name__)

# 配置
app.config['SECRET_KEY'] = 'rrt-visualizer-secret-key-change-this-in-production'  # 更改为更安全的密钥
app.config['JSON_SORT_KEYS'] = False  # 保持JSON响应的键顺序
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # 会话持续7天

# 用户数据文件路径
USER_DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'users.json')

# 确保data目录存在
os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)

# 创建配置空间及算法实例
config_space = ConfigurationSpace(800, 600)
algorithms = {
    "BaseRRT": BaseRRT(
        [0, 0], [0, 0], config_space,
        step_size=20, goal_sample_rate=0.05, max_iter=1000
    ),
    "RRTStar": RRTStar(
        [0, 0], [0, 0], config_space,
        step_size=20, goal_sample_rate=0.05, max_iter=3000, search_radius=50
    ),
    "RRTConnect": RRTConnect(
        [0, 0], [0, 0], config_space,
        step_size=20, max_iter=1500
    ),
    "InformedRRT": InformedRRT(
        [0, 0], [0, 0], config_space,
        step_size=20, goal_sample_rate=0.05, max_iter=3000, search_radius=50
    )
}


# 认证函数
def hash_password(password, salt=None):
    """密码哈希处理"""
    if salt is None:
        salt = secrets.token_hex(16)
    pw_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return pw_hash, salt


def load_users():
    """从文件中加载用户数据"""
    if not os.path.exists(USER_DATA_FILE):
        return {}
    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_users(users):
    """将用户数据保存到文件"""
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f, indent=4)


def register_user(username, password, email):
    """注册新用户"""
    users = load_users()

    if username in users:
        return False, "用户名已被使用"

    for user in users.values():
        if user.get('email') == email:
            return False, "邮箱已被注册"

    pw_hash, salt = hash_password(password)

    users[username] = {
        'username': username,
        'password_hash': pw_hash,
        'salt': salt,
        'email': email,
        'created_at': datetime.now().isoformat(),
        'last_login': None,
        'preferences': {}
    }

    save_users(users)
    return True, "注册成功！"


def verify_user(username, password):
    """验证用户登录"""
    users = load_users()

    if username not in users:
        return False, "用户名或密码不正确"

    user = users[username]

    pw_hash, _ = hash_password(password, user['salt'])
    if pw_hash != user['password_hash']:
        return False, "用户名或密码不正确"

    user['last_login'] = datetime.now().isoformat()
    save_users(users)

    return True, user


def is_logged_in():
    """检查用户是否已登录"""
    return 'user_id' in session


def get_current_user():
    """获取当前登录用户的信息"""
    if not is_logged_in():
        return None

    users = load_users()
    return users.get(session['user_id'])


def login_required(view_func):
    """用于视图函数的登录验证装饰器"""

    def wrapper(*args, **kwargs):
        if not is_logged_in():
            session['next_url'] = request.url
            flash('请先登录再访问此页面', 'warning')
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)

    wrapper.__name__ = view_func.__name__
    return wrapper


def update_user_preferences(username, preferences):
    """更新用户偏好设置"""
    users = load_users()

    if username not in users:
        return False

    users[username]['preferences'] = preferences
    save_users(users)

    return True


# 在每个请求之前执行
@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = get_current_user()


# 主页
@app.route('/')
def index():
    return render_template('index.html')


# 关于页面
@app.route('/about')
def about():
    return render_template('about.html')


# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'

        success, result = verify_user(username, password)

        if success:
            session['user_id'] = username

            if remember:
                session.permanent = True

            flash('登录成功！', 'success')

            next_url = session.pop('next_url', None)
            if next_url:
                return redirect(next_url)

            return redirect(url_for('index'))
        else:
            flash(result, 'danger')

    return render_template('login.html')


# 注册页面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if is_logged_in():
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        email = request.form.get('email')

        # 验证输入
        if not username or len(username) < 3:
            flash('用户名至少需要3个字符', 'danger')
        elif not password or len(password) < 6:
            flash('密码至少需要6个字符', 'danger')
        elif password != password_confirm:
            flash('两次输入的密码不匹配', 'danger')
        elif not email or '@' not in email:
            flash('请输入有效的电子邮箱', 'danger')
        else:
            success, message = register_user(username, password, email)

            if success:
                flash(message, 'success')
                return redirect(url_for('login'))
            else:
                flash(message, 'danger')

    return render_template('register.html')


# 注销
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('您已成功注销', 'success')
    return redirect(url_for('index'))


# 个人资料页面
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=g.user)


# 保存用户偏好设置
@app.route('/save-preferences', methods=['POST'])
@login_required
def save_preferences():
    if not g.user:
        return jsonify({'success': False, 'message': '未登录'}), 401

    preferences = {
        'defaultAlgorithm': request.form.get('defaultAlgorithm', 'BaseRRT'),
        'defaultStepSize': int(request.form.get('defaultStepSize', 20)),
        'defaultMaxIterations': int(request.form.get('defaultMaxIterations', 1000)),
        'defaultGoalSampleRate': float(request.form.get('defaultGoalSampleRate', 0.05)),
        'showGrid': request.form.get('showGrid') == 'on',
        'animationEnabled': request.form.get('animationEnabled') == 'on'
    }

    success = update_user_preferences(g.user['username'], preferences)

    if success:
        flash('偏好设置已保存', 'success')
    else:
        flash('保存偏好设置失败', 'danger')

    return redirect(url_for('profile'))


# 修改密码
@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    if not g.user:
        return jsonify({'success': False, 'message': '未登录'}), 401

    current_password = request.form.get('currentPassword')
    new_password = request.form.get('newPassword')
    confirm_password = request.form.get('confirmPassword')

    if not current_password or not new_password or not confirm_password:
        flash('所有密码字段都必须填写', 'danger')
        return redirect(url_for('profile'))

    if new_password != confirm_password:
        flash('新密码与确认密码不匹配', 'danger')
        return redirect(url_for('profile'))

    if len(new_password) < 6:
        flash('新密码至少需要6个字符', 'danger')
        return redirect(url_for('profile'))

    # 验证当前密码
    users = load_users()
    user = users.get(g.user['username'])

    if not user:
        flash('用户不存在', 'danger')
        return redirect(url_for('profile'))

    current_hash, _ = hash_password(current_password, user['salt'])

    if current_hash != user['password_hash']:
        flash('当前密码不正确', 'danger')
        return redirect(url_for('profile'))

    # 更新密码
    new_hash, new_salt = hash_password(new_password)
    user['password_hash'] = new_hash
    user['salt'] = new_salt

    save_users(users)

    flash('密码已成功更改', 'success')
    return redirect(url_for('profile'))


# API: 执行规划
@app.route('/api/plan', methods=['POST'])
def plan():
    try:
        # 获取请求数据
        data = request.json

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # 验证必需参数
        required_fields = ['start', 'goal', 'algorithm', 'obstacles', 'parameters']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # 提取参数
        start = data['start']
        goal = data['goal']
        algorithm_name = data['algorithm']
        obstacles_data = data['obstacles']
        parameters = data['parameters']

        # 验证算法名称
        if algorithm_name not in algorithms:
            return jsonify({'error': f'Unknown algorithm: {algorithm_name}'}), 400

        # 重置配置空间
        global config_space
        config_space = ConfigurationSpace(800, 600)

        # 添加障碍物
        for obs in obstacles_data:
            if obs['type'] == 'rectangle':
                obstacle = RectangleObstacle(
                    obs['x'], obs['y'], obs['width'], obs['height']
                )
            elif obs['type'] == 'circle':
                obstacle = CircleObstacle(
                    obs['centerX'], obs['centerY'], obs['radius']
                )
            else:
                continue

            config_space.add_obstacle(obstacle)

        # 更新算法参数
        algorithm = algorithms[algorithm_name]
        algorithm.start = np.array(start)
        algorithm.goal = np.array(goal)
        algorithm.config_space = config_space

        if 'stepSize' in parameters:
            algorithm.step_size = parameters['stepSize']
        if 'maxIter' in parameters:
            algorithm.max_iter = parameters['maxIter']
        if 'goalSampleRate' in parameters and hasattr(algorithm, 'goal_sample_rate'):
            algorithm.goal_sample_rate = parameters['goalSampleRate']
        if 'searchRadius' in parameters and hasattr(algorithm, 'search_radius'):
            algorithm.search_radius = parameters['searchRadius']

        # 执行规划
        result = algorithm.plan()

        # 转换NumPy数组为Python列表，以便JSON序列化
        serializable_result = numpy_to_list(result)

        # 添加算法详细信息到结果中
        serializable_result['details'] = numpy_to_list(algorithm.get_details())

        return jsonify(serializable_result)

    except Exception as e:
        app.logger.error(f"Error in plan endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500


# API: 获取支持的算法
@app.route('/api/algorithms', methods=['GET'])
def get_algorithms():
    return jsonify(list(algorithms.keys()))


# API: 获取预设场景列表
@app.route('/api/presets', methods=['GET'])
def get_presets():
    preset_info = {}
    for key, preset in PRESETS.items():
        preset_info[key] = preset.get_metadata()
    return jsonify(preset_info)


# API: 获取特定预设场景
@app.route('/api/presets/<preset_id>', methods=['GET'])
def get_preset(preset_id):
    if preset_id not in PRESETS:
        return jsonify({'error': f'Unknown preset: {preset_id}'}), 404

    preset = PRESETS[preset_id]
    space = preset.create_space()

    # 收集场景信息
    obstacles = []
    for obs in space.obstacles:
        if obs.get_type() == 'rectangle':
            x, y, width, height = obs.get_boundary()
            obstacles.append({
                'type': 'rectangle',
                'x': x,
                'y': y,
                'width': width,
                'height': height
            })
        elif obs.get_type() == 'circle':
            centerX, centerY, radius = obs.get_boundary()
            obstacles.append({
                'type': 'circle',
                'centerX': centerX,
                'centerY': centerY,
                'radius': radius
            })

    # 构建响应
    response = {
        'metadata': preset.get_metadata(),
        'obstacles': obstacles
    }

    return jsonify(response)


# 自定义上下文处理器，将用户对象添加到所有模板中
@app.context_processor
def inject_user():
    return {'user': g.user}


# 启动应用
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)