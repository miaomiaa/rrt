#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RRTVisualizer-Web - Web应用主文件
一个基于Web的路径规划算法可视化应用程序
"""

import os
import json
import numpy as np
from flask import Flask, render_template, request, jsonify, abort, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import timedelta
# 导入算法
from algorithms import BaseRRT, RRTStar, RRTConnect, InformedRRT
from environment import ConfigurationSpace, RectangleObstacle, CircleObstacle, PolygonObstacle, PRESETS
from utils.converter import numpy_to_list
from auth import UserManager
# 创建Flask应用
app = Flask(__name__)

# 配置
app.config['SECRET_KEY'] = 'rrt-visualizer-secret-key'
app.config['JSON_SORT_KEYS'] = False  # 保持JSON响应的键顺序
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # 会话持续时间

user_manager = UserManager()
# 登录保护装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录以访问该页面', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

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


# 主页 - 修改为检查登录状态
@app.route('/')
def index():
    # 检查用户是否登录
    user = None
    if 'user_id' in session:
        username = session.get('username')
        user = user_manager.get_user(username)

    return render_template('index.html', user=user)


# 关于页面 - 修改为检查登录状态
@app.route('/about')
def about():
    # 检查用户是否登录
    user = None
    if 'user_id' in session:
        username = session.get('username')
        user = user_manager.get_user(username)

    return render_template('about.html', user=user)


# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    # 如果用户已登录，重定向到主页
    if 'user_id' in session:
        return redirect(url_for('index'))

    # 处理登录表单提交
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form

        # 验证用户凭据
        user = user_manager.authenticate(username, password)

        if user:
            # 登录成功，创建会话
            session['user_id'] = user.user_id
            session['username'] = user.username

            # 如果用户选择"记住我"，设置会话为永久
            if remember:
                session.permanent = True

            flash('登录成功！', 'success')

            # 如果有next参数，重定向到之前尝试访问的页面
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)

            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误', 'danger')

    return render_template('login.html')


# 注册页面
@app.route('/register', methods=['GET', 'POST'])
def register():
    # 如果用户已登录，重定向到主页
    if 'user_id' in session:
        return redirect(url_for('index'))

    # 处理注册表单提交
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # 验证密码是否匹配
        if password != confirm_password:
            flash('两次输入的密码不匹配', 'danger')
            return render_template('register.html')

        # 创建新用户
        user = user_manager.create_user(username, email, password)

        if user:
            flash('注册成功！请登录', 'success')
            return redirect(url_for('login'))
        else:
            flash('注册失败，用户名或邮箱已被使用', 'danger')

    return render_template('register.html')


# 退出登录
@app.route('/logout')
def logout():
    # 清除会话
    session.pop('user_id', None)
    session.pop('username', None)
    session.permanent = False

    flash('您已成功退出登录', 'success')
    return redirect(url_for('login'))


# 个人资料页面
@app.route('/profile')
@login_required
def profile():
    username = session.get('username')
    user = user_manager.get_user(username)

    if not user:
        flash('用户不存在', 'danger')
        return redirect(url_for('logout'))

    # 获取用户配置
    configs = user_manager.get_user_configs(username)

    return render_template('profile.html', user=user, configs=configs)


# 更新个人资料
@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    username = session.get('username')
    email = request.form['email']

    # 更新用户信息
    success = user_manager.update_user(username, email=email)

    if success:
        flash('个人资料已更新', 'success')
    else:
        flash('更新个人资料失败', 'danger')

    return redirect(url_for('profile'))


# 修改密码
@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    username = session.get('username')
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']

    # 验证当前密码
    user = user_manager.get_user(username)
    if not user or not user.check_password(current_password):
        flash('当前密码不正确', 'danger')
        return redirect(url_for('profile'))

    # 验证新密码是否匹配
    if new_password != confirm_password:
        flash('两次输入的新密码不匹配', 'danger')
        return redirect(url_for('profile'))

    # 更新密码
    success = user_manager.update_user(username, password=new_password)

    if success:
        flash('密码已成功修改', 'success')
    else:
        flash('修改密码失败', 'danger')

    return redirect(url_for('profile'))


# 保存配置
@app.route('/save_config', methods=['POST'])
@login_required
def save_config():
    data = request.json
    username = session.get('username')

    config_name = data.get('config_name')
    config_data = data.get('config_data')

    if not config_name or not config_data:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400

    # 保存配置
    success = user_manager.save_user_config(username, config_name, config_data)

    if success:
        return jsonify({'success': True, 'message': '配置已保存'})
    else:
        return jsonify({'success': False, 'message': '保存配置失败'}), 500


# 获取用户配置列表
@app.route('/get_user_configs')
@login_required
def get_user_configs():
    username = session.get('username')
    configs = user_manager.get_user_configs(username)
    return jsonify(configs)


# 加载配置
@app.route('/load_config/<config_name>')
@login_required
def load_config(config_name):
    username = session.get('username')
    config = user_manager.get_user_config(username, config_name)

    if not config:
        flash('配置不存在', 'danger')
        return redirect(url_for('index'))

    # 将配置存储在会话中，以便在页面加载时使用
    session['loaded_config'] = {
        'name': config_name,
        'data': config['data']
    }

    flash(f'配置"{config_name}"已加载', 'success')
    return redirect(url_for('index'))


# 删除配置
@app.route('/delete_config', methods=['POST'])
@login_required
def delete_config():
    username = session.get('username')
    config_name = request.form['config_name']

    # 删除配置
    success = user_manager.delete_user_config(username, config_name)

    if success:
        flash(f'配置"{config_name}"已删除', 'success')
    else:
        flash('删除配置失败', 'danger')

    return redirect(url_for('profile'))


# 检查用户名可用性 API
@app.route('/check_username')
def check_username():
    username = request.args.get('username', '')

    if not username:
        return jsonify({'available': False})

    # 检查用户名是否已存在
    user = user_manager.get_user(username)

    return jsonify({'available': user is None})



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


# 启动应用
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)